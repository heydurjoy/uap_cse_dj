"""
Django signals for media file compression and validation.
"""
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.conf import settings
from people.utils.media_processing import compress_image, validate_pdf_size, delete_file_safely


def get_image_field_mapping():
    """Get image field mapping with settings (lazy loading)."""
    from people.models import (
        BaseUser, Faculty, Staff, Officer, ClubMember, Contributor
    )
    from clubs.models import Club
    from designs.models import FeatureCard
    from office.models import ClassRoutine
    
    return {
        # Profile pictures
        (BaseUser, 'profile_picture'): settings.MEDIA_SIZE_LIMITS['profile_pictures'],
        (Faculty, 'profile_pic'): settings.MEDIA_SIZE_LIMITS['profile_pictures'],
        (Staff, 'profile_pic'): settings.MEDIA_SIZE_LIMITS['profile_pictures'],
        (Officer, 'profile_pic'): settings.MEDIA_SIZE_LIMITS['profile_pictures'],
        (ClubMember, 'profile_pic'): settings.MEDIA_SIZE_LIMITS['profile_pictures'],
        (Contributor, 'photo'): settings.MEDIA_SIZE_LIMITS['profile_pictures'],
        
        # Club assets
        (Club, 'logo'): settings.MEDIA_SIZE_LIMITS['club_logos'],
        (Club, 'cover_photo'): settings.MEDIA_SIZE_LIMITS['club_covers'],
        
        # Feature cards
        (FeatureCard, 'picture'): settings.MEDIA_SIZE_LIMITS['feature_cards'],
        
        # Class routines
        (ClassRoutine, 'routine_image'): settings.MEDIA_SIZE_LIMITS['class_routines'],
    }


def get_pdf_field_mapping():
    """Get PDF field mapping with settings (lazy loading)."""
    from people.models import Faculty
    from designs.models import AdmissionElement, AcademicCalendar
    from office.models import PostAttachment, AdmissionResult
    from academics.models import Course
    
    return {
        (Faculty, 'cv'): settings.PDF_SIZE_LIMITS['faculty_cv'],
        (AdmissionElement, 'curriculum_pdf'): settings.PDF_SIZE_LIMITS['curriculum_pdf'],
        (AcademicCalendar, 'pdf'): settings.PDF_SIZE_LIMITS['academic_calendar'],
        (AdmissionResult, 'official_pdf'): settings.PDF_SIZE_LIMITS['admission_result'],
        (PostAttachment, 'file'): settings.PDF_SIZE_LIMITS['post_attachment'],
        (Course, 'course_outline_pdf'): settings.PDF_SIZE_LIMITS['course_outline'],
    }


@receiver(pre_save)
def compress_image_files(sender, instance, **kwargs):
    """
    Compress image files before saving if they exceed size thresholds.
    Only processes if file is new or has been changed.
    """
    # Get mapping (lazy load to avoid import issues during Django setup)
    IMAGE_FIELD_MAPPING = get_image_field_mapping()
    
    # Check if this model has any image fields we need to process
    for (model_class, field_name), settings_dict in IMAGE_FIELD_MAPPING.items():
        if isinstance(instance, model_class):
            field = getattr(instance, field_name, None)
            if not field:
                continue
            
            # Check if file exists (new upload or existing file)
            has_file = False
            if hasattr(field, 'file') and field.file:
                # New upload
                has_file = True
            elif hasattr(field, 'name') and field.name:
                # Existing file or new upload with name
                has_file = True
            
            if not has_file:
                continue
            
            # Check if this is a new file or changed file
            file_changed = True
            old_field = None
            if instance.pk:
                try:
                    old_instance = model_class.objects.get(pk=instance.pk)
                    old_field = getattr(old_instance, field_name, None)
                    if old_field:
                        old_name = getattr(old_field, 'name', None) if old_field else None
                        new_name = getattr(field, 'name', None) if field else None
                        # File hasn't changed if names match and it's not a new upload
                        if old_name == new_name and not (hasattr(field, 'file') and field.file):
                            file_changed = False
                except model_class.DoesNotExist:
                    pass
            
            if not file_changed:
                continue
            
            # Delete old file if it's being replaced
            if old_field and old_field.name:
                old_name = getattr(old_field, 'name', None)
                new_name = getattr(field, 'name', None) if field else None
                # If file names are different, delete the old one
                if old_name != new_name:
                    delete_file_safely(old_field)
            
            # Apply compression
            compress_image(
                file_field=field,
                max_size_kb=settings_dict['max_size_kb'],
                target_dimensions=settings_dict.get('target_dimensions'),
                quality=settings_dict.get('quality', 85),
                max_width=settings_dict.get('max_width'),
                max_height=settings_dict.get('max_height'),
            )
            break


@receiver(pre_save)
def validate_pdf_files(sender, instance, **kwargs):
    """
    Validate PDF file sizes before saving.
    Raises ValidationError if file exceeds size limit.
    """
    # Get mapping (lazy load to avoid import issues during Django setup)
    PDF_FIELD_MAPPING = get_pdf_field_mapping()
    
    # Check if this model has any PDF fields we need to validate
    for (model_class, field_name), max_size_mb in PDF_FIELD_MAPPING.items():
        if isinstance(instance, model_class):
            field = getattr(instance, field_name, None)
            if not field:
                continue
            
            # Check if file exists (new upload or existing file)
            has_file = False
            if hasattr(field, 'file') and field.file:
                # New upload
                has_file = True
            elif hasattr(field, 'name') and field.name:
                # Existing file or new upload with name
                has_file = True
            
            if not has_file:
                continue
            
            # Check if this is a new file or changed file
            file_changed = True
            if instance.pk:
                try:
                    old_instance = model_class.objects.get(pk=instance.pk)
                    old_field = getattr(old_instance, field_name, None)
                    if old_field:
                        old_name = getattr(old_field, 'name', None) if old_field else None
                        new_name = getattr(field, 'name', None) if field else None
                        # File hasn't changed if names match and it's not a new upload
                        if old_name == new_name and not (hasattr(field, 'file') and field.file):
                            file_changed = False
                except model_class.DoesNotExist:
                    pass
            
            if not file_changed:
                continue
            
            # Validate PDF size
            try:
                validate_pdf_size(field, max_size_mb)
            except ValidationError as e:
                # Re-raise validation error
                raise e
            break


@receiver(post_delete)
def delete_media_files(sender, instance, **kwargs):
    """
    Delete associated media files when objects are deleted.
    This prevents orphaned files from accumulating in storage.
    """
    # Get all field mappings
    IMAGE_FIELD_MAPPING = get_image_field_mapping()
    PDF_FIELD_MAPPING = get_pdf_field_mapping()
    
    # Check if this model has any file fields we need to clean up
    all_field_mappings = list(IMAGE_FIELD_MAPPING.keys()) + list(PDF_FIELD_MAPPING.keys())
    
    # Process all file fields for this model instance
    for (model_class, field_name) in all_field_mappings:
        if isinstance(instance, model_class):
            field = getattr(instance, field_name, None)
            if field:
                # Delete the file
                delete_file_safely(field)

