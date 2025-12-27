from django.db import models
from django.core.files.base import ContentFile
from ckeditor.fields import RichTextField
from django.urls import reverse
from image_cropping.fields import ImageRatioField, ImageCropField
from PIL import Image
import io
import os

class FeatureCard(models.Model):
    sl_number = models.IntegerField(unique=True, help_text="Serial number for ordering")
    picture = ImageCropField(upload_to='feature_cards/', help_text="Main picture for the card (Max 600KB, will be compressed and resized to 600x600px if larger)")
    cropping = ImageRatioField('picture', '600x600', size_warning=True, help_text="Crop image to 1:1 aspect ratio (600x600)")
    caption = models.CharField(max_length=200, help_text="Short caption displayed on the card")
    title = models.CharField(max_length=200, help_text="Title for the detail page")
    description = RichTextField(help_text="Detailed description with rich text formatting")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Show/hide this card")
    
    class Meta:
        ordering = ['sl_number']
        verbose_name = 'Feature Card'
        verbose_name_plural = 'Feature Cards'
    
    def __str__(self):
        return f"{self.sl_number} - {self.caption}"
    
    def get_absolute_url(self):
        return reverse('designs:feature_card_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        is_update = self.pk is not None
        # Detect if picture file was replaced
        picture_changed = False
        if is_update:
            try:
                old = FeatureCard.objects.get(pk=self.pk)
                picture_changed = old.picture.name != self.picture.name
            except FeatureCard.DoesNotExist:
                picture_changed = False
        else:
            picture_changed = True

        cropping_set = bool(self.picture and self.cropping and self.cropping.strip())

        # Only apply cropping when coords exist AND the picture hasn't just been changed.
        # This prevents aggressive cropping on first upload or when replacing an image.
        # Admins can crop after saving the new image.
        if cropping_set and is_update and not picture_changed:
            try:
                # Get the original image path
                if self.picture.name:
                    # Read the image file
                    if hasattr(self.picture, 'read'):
                        self.picture.seek(0)
                        image_data = self.picture.read()
                    else:
                        image_path = self.picture.path
                        with open(image_path, 'rb') as f:
                            image_data = f.read()
                    
                    # Open image with PIL from bytes
                    image = Image.open(io.BytesIO(image_data))
                    
                    # Parse cropping coordinates (format: "x1,y1,x2,y2")
                    crop_coords = [int(x.strip()) for x in self.cropping.split(',')]
                    if len(crop_coords) == 4:
                        x1, y1, x2, y2 = crop_coords
                        
                        # Crop the image
                        cropped_image = image.crop((x1, y1, x2, y2))
                        
                        # Resize to exact 400x400 if needed
                        if cropped_image.size != (400, 400):
                            cropped_image = cropped_image.resize((400, 400), Image.Resampling.LANCZOS)
                        
                        # Save to memory
                        img_io = io.BytesIO()
                        # Determine format from original
                        format = image.format or 'JPEG'
                        if format not in ['JPEG', 'PNG', 'WEBP']:
                            format = 'JPEG'
                        
                        # Convert RGBA to RGB if necessary for JPEG
                        if format == 'JPEG' and cropped_image.mode in ('RGBA', 'LA', 'P'):
                            rgb_image = Image.new('RGB', cropped_image.size, (255, 255, 255))
                            if cropped_image.mode == 'P':
                                cropped_image = cropped_image.convert('RGBA')
                            rgb_image.paste(cropped_image, mask=cropped_image.split()[-1] if cropped_image.mode == 'RGBA' else None)
                            cropped_image = rgb_image
                        
                        cropped_image.save(img_io, format=format, quality=95)
                        img_io.seek(0)
                        
                        # Replace the original file
                        file_name = os.path.basename(self.picture.name)
                        self.picture.save(
                            file_name,
                            ContentFile(img_io.read()),
                            save=False
                        )
                        
                        # Clear cropping coordinates after applying
                        self.cropping = ''
                        
            except Exception as e:
                # If cropping fails, just save normally
                import traceback
                traceback.print_exc()
        
        super().save(*args, **kwargs)

class HeroTags(models.Model):
    sl = models.IntegerField(unique=True, help_text="Serial number for ordering")
    title = models.CharField(max_length=20, help_text="Tag title (max 20 characters)")
    is_active = models.BooleanField(default=True, help_text="Show this tag on the website")
    
    class Meta:
        ordering = ['sl']
        verbose_name = 'Hero Tag'
        verbose_name_plural = 'Hero Tags'
    
    def __str__(self):
        return f"{self.sl} - {self.title}"

class AdmissionElement(models.Model):
    sl = models.IntegerField(unique=True, help_text="Serial number for ordering")
    title = models.CharField(max_length=200, help_text="Title for the admission element")
    content = RichTextField(help_text="Rich text content for the admission element")
    curriculum_pdf = models.FileField(
        upload_to='admission/curricula/',
        blank=True,
        null=True,
        help_text="Upload curriculum PDF (for BSc and MCSE programs, Max 10MB)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sl']
        verbose_name = 'Admission Element'
        verbose_name_plural = 'Admission Elements'
    
    def __str__(self):
        return f"{self.sl} - {self.title}"


class AcademicCalendar(models.Model):
    """Academic calendar with year/term and PDF file"""
    year = models.CharField(
        max_length=100,
        unique=True,
        help_text="Academic year or term (e.g., '2025' or 'Spring 2025')"
    )
    pdf = models.FileField(
        upload_to='academic_calendars/',
        help_text="PDF file for the academic calendar (Max 5MB)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Academic Calendar'
        verbose_name_plural = 'Academic Calendars'
    
    def __str__(self):
        return f"Academic Calendar {self.year}"


class Curricula(models.Model):
    """Curriculum documents with versioning"""
    SEMESTER_CHOICES = [
        ('spring', 'Spring'),
        ('fall', 'Fall'),
    ]
    
    short_title = models.CharField(
        max_length=50,
        help_text="Short title for the curriculum (max 50 characters)"
    )
    program = models.ForeignKey(
        'academics.Program',
        on_delete=models.CASCADE,
        related_name='curricula',
        help_text="Program this curriculum belongs to"
    )
    publishing_year = models.IntegerField(
        help_text="Year when the curriculum was published"
    )
    version = models.FloatField(
        help_text="Version number of the curriculum (e.g., 1.0, 2.5)"
    )
    running_since_year = models.CharField(
        max_length=10,
        default='2024',
        help_text="Year when this curriculum started running (e.g., '2024')"
    )
    running_since_semester = models.CharField(
        max_length=10,
        choices=SEMESTER_CHOICES,
        default='spring',
        help_text="Semester when this curriculum started running (Spring comes before Fall)"
    )
    pdf = models.FileField(
        upload_to='curricula/',
        help_text="PDF file of the curriculum (Max 10MB)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Note: Custom ordering with Spring before Fall is handled in views using annotate
        # Default ordering here is a fallback
        ordering = ['program', '-running_since_year', 'running_since_semester', '-version']
        verbose_name = 'Curriculum'
        verbose_name_plural = 'Curricula'
        unique_together = [['short_title', 'program', 'publishing_year', 'version', 'running_since_year', 'running_since_semester']]
    
    def __str__(self):
        semester_display = dict(self.SEMESTER_CHOICES).get(self.running_since_semester, self.running_since_semester)
        return f"{self.program.name} - {self.short_title} (Running since {semester_display} {self.running_since_year}) - v{self.version}"
    
    def get_running_since_display(self):
        """Get formatted running since string"""
        semester_display = dict(self.SEMESTER_CHOICES).get(self.running_since_semester, self.running_since_semester)
        return f"{semester_display} {self.running_since_year}"