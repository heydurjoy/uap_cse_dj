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
        """
        Simplified save: no manual image/cropping handling.
        We just let Django store the uploaded file as-is to avoid
        file handle/seek issues and keep behavior predictable.
        """
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