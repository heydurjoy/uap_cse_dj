"""
Media processing utilities for image compression and PDF validation.
"""
from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
import io
import os
import uuid


def get_file_size_mb(file):
    """Get file size in MB."""
    if hasattr(file, 'size'):
        return file.size / (1024 * 1024)
    elif hasattr(file, 'read'):
        current_pos = file.tell()
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(current_pos)
        return size / (1024 * 1024)
    return 0


def get_file_size_kb(file):
    """Get file size in KB."""
    if hasattr(file, 'size'):
        return file.size / 1024
    elif hasattr(file, 'read'):
        current_pos = file.tell()
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(current_pos)
        return size / 1024
    return 0


def resize_image(image, max_width=None, max_height=None, target_size=None):
    """
    Resize image maintaining aspect ratio.
    
    Args:
        image: PIL Image object
        max_width: Maximum width (maintains aspect ratio)
        max_height: Maximum height (maintains aspect ratio)
        target_size: Tuple (width, height) for exact resize
    
    Returns:
        Resized PIL Image
    """
    if target_size:
        return image.resize(target_size, Image.Resampling.LANCZOS)
    
    width, height = image.size
    
    if max_width and width > max_width:
        ratio = max_width / width
        new_width = max_width
        new_height = int(height * ratio)
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    if max_height and height > max_height:
        ratio = max_height / height
        new_width = int(width * ratio)
        new_height = max_height
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return image


def compress_image(file_field, max_size_kb, target_dimensions=None, quality=85, max_width=None, max_height=None):
    """
    Compress image if it exceeds the size threshold.
    
    Args:
        file_field: Django FileField or ImageField
        max_size_kb: Maximum file size in KB (compression threshold)
        target_dimensions: Tuple (width, height) for exact resize
        quality: JPEG quality (1-100)
        max_width: Maximum width (maintains aspect ratio)
        max_height: Maximum height (maintains aspect ratio)
    
    Returns:
        True if compression was applied, False otherwise
    """
    if not file_field:
        return False
    
    # Check if file has content (for new uploads, check if file object exists)
    if hasattr(file_field, 'file'):
        # New upload - file is in memory
        if not hasattr(file_field.file, 'read'):
            return False
        file_field.file.seek(0)
        image_data = file_field.file.read()
        file_field.file.seek(0)
    elif hasattr(file_field, 'read'):
        # File object with read method
        file_field.seek(0)
        image_data = file_field.read()
        file_field.seek(0)
    elif hasattr(file_field, 'path') and file_field.name:
        # Existing file on disk
        try:
            image_path = file_field.path
            with open(image_path, 'rb') as f:
                image_data = f.read()
        except (ValueError, FileNotFoundError):
            return False
    else:
        return False
    
    # Check current file size
    current_size_kb = len(image_data) / 1024
    
    # If already below threshold, skip compression
    if current_size_kb <= max_size_kb:
        return False
    
    try:
        
        # Open image with PIL
        image = Image.open(io.BytesIO(image_data))
        original_format = image.format or 'JPEG'
        
        # Convert format if needed
        if original_format not in ['JPEG', 'PNG', 'WEBP']:
            original_format = 'JPEG'
        
        # Resize if needed
        if target_dimensions:
            image = resize_image(image, target_size=target_dimensions)
        elif max_width or max_height:
            image = resize_image(image, max_width=max_width, max_height=max_height)
        
        # Convert RGBA to RGB if necessary for JPEG
        if original_format == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = rgb_image
        
        # Compress and save to memory
        img_io = io.BytesIO()
        
        # Adjust quality iteratively if needed to meet size requirement
        current_quality = quality
        max_iterations = 10
        
        for _ in range(max_iterations):
            img_io.seek(0)
            img_io.truncate(0)
            
            if original_format == 'PNG':
                # PNG compression
                image.save(img_io, format='PNG', optimize=True, compress_level=9)
            else:
                # JPEG compression
                image.save(img_io, format='JPEG', quality=current_quality, optimize=True)
            
            img_io.seek(0)
            compressed_size_kb = len(img_io.getvalue()) / 1024
            
            if compressed_size_kb <= max_size_kb or current_quality <= 50:
                break
            
            # Reduce quality for next iteration
            current_quality -= 5
        
        # Replace the file
        img_io.seek(0)
        compressed_data = img_io.read()
        
        # Save the compressed image back to the file field
        if hasattr(file_field, 'file'):
            # New upload - replace the file object
            file_name = file_field.name if hasattr(file_field, 'name') and file_field.name else f"compressed_{uuid.uuid4()}.jpg"
            file_name = os.path.basename(file_name)
            
            # Create new file object
            new_file = ContentFile(compressed_data)
            file_field.file = new_file
            if hasattr(file_field, 'name'):
                file_field.name = file_name
        elif hasattr(file_field, 'save'):
            # FileField with save method
            file_name = os.path.basename(file_field.name) if hasattr(file_field, 'name') and file_field.name else f"compressed_{uuid.uuid4()}.jpg"
            file_field.save(
                file_name,
                ContentFile(compressed_data),
                save=False
            )
        elif hasattr(file_field, 'path'):
            # File path - write directly
            with open(file_field.path, 'wb') as f:
                f.write(compressed_data)
        
        return True
        
    except Exception as e:
        # If compression fails, log error but don't break the save
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Image compression failed: {str(e)}")
        return False


def validate_pdf_size(file_field, max_size_mb):
    """
    Validate PDF file size and raise ValidationError if exceeds limit.
    
    Args:
        file_field: Django FileField
        max_size_mb: Maximum file size in MB
    
    Raises:
        ValidationError: If file exceeds size limit
    """
    if not file_field or not file_field.name:
        return
    
    file_size_mb = get_file_size_mb(file_field)
    
    if file_size_mb > max_size_mb:
        raise ValidationError(
            f'File size ({file_size_mb:.2f} MB) exceeds maximum allowed size of {max_size_mb} MB.'
        )

