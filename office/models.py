from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from ckeditor.fields import RichTextField
from people.models import BaseUser
from datetime import datetime
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile


def validate_thumbnail_size(value):
    """Validate that thumbnail image is not larger than 1 MB"""
    if value.size > 1024 * 1024:  # 1 MB in bytes
        raise ValidationError('Thumbnail image size cannot exceed 1 MB.')


# Semester Choices for Admission Results
SEMESTER_CHOICES = (
    ('Fall', 'Fall'),
    ('Spring', 'Spring'),
)

# Year-Semester Choices
YEAR_SEMESTER_CHOICES = (
    ('1-1', 'Year 1, Semester 1'),
    ('1-2', 'Year 1, Semester 2'),
    ('2-1', 'Year 2, Semester 1'),
    ('2-2', 'Year 2, Semester 2'),
    ('3-1', 'Year 3, Semester 1'),
    ('3-2', 'Year 3, Semester 2'),
    ('4-1', 'Year 4, Semester 1'),
    ('4-2', 'Year 4, Semester 2'),
)

# Section Choices
SECTION_CHOICES = (
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
    ('E', 'E'),
    ('F', 'F'),
    ('G', 'G'),
    ('H', 'H'),
    ('I', 'I'),
    ('J', 'J'),
)

# Exam Type Choices
EXAM_TYPE_CHOICES = (
    ('mid', 'Mid'),
    ('final', 'Final'),
)

# Section Choices for Exam Routines (A-E only)
EXAM_SECTION_CHOICES = (
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
    ('E', 'E'),
)

# Post Type Choices
POST_TYPE_CHOICES = (
    ('notice', 'Notice'),
    ('events', 'Events'),
    ('seminars', 'Seminars'),
    ('workshop', 'Workshop'),
    ('others', 'Others'),
)


class AdmissionResult(models.Model):
    """
    Model for posting admission test results.
    Only authorized staff (Officer/Faculty) with User Level >= 3 can create posts.
    """
    publish_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Publish Date/Time",
        help_text="Records when the result was posted"
    )
    academic_year = models.SmallIntegerField(
        verbose_name="Academic Year",
        help_text="Numerical year (e.g., 2026)"
    )
    semester = models.CharField(
        max_length=10,
        choices=SEMESTER_CHOICES,
        verbose_name="Semester",
        help_text="Fixed choices: Fall or Spring"
    )
    slot = models.IntegerField(
        verbose_name="Slot",
        help_text="The specific admission slot (e.g., 1, 2, 3)"
    )
    result_content = RichTextField(
        verbose_name="Result Content",
        help_text="Main body displayed on the webpage"
    )
    official_pdf = models.FileField(
        upload_to='admission_results/',
        verbose_name="Official PDF",
        help_text="Single file for the official, signed result document (Max 10MB)"
    )
    created_by = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_admission_results',
        verbose_name="Created By",
        help_text="Links to the existing authorized user who created the post"
    )
    created_by_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Created By Name",
        help_text="Name of the user who created this result (preserved even if user is deleted)"
    )
    created_by_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Created By Email",
        help_text="Email of the user who created this result (preserved even if user is deleted)"
    )

    class Meta:
        verbose_name = 'Admission Result'
        verbose_name_plural = 'Admission Results'
        ordering = ['-publish_date', '-academic_year', 'semester', 'slot']
        # Ensure unique combination of academic_year, semester, and slot
        unique_together = ('academic_year', 'semester', 'slot')

    def __str__(self):
        return f"{self.academic_year} {self.semester} - Slot {self.slot}"
    
    def save(self, *args, **kwargs):
        """Auto-populate created_by_name and created_by_email when created_by is set"""
        if self.created_by and not self.created_by_name:
            # Get the user's name based on their type
            name = None
            email = self.created_by.email or ''
            
            if self.created_by.user_type == 'faculty' and hasattr(self.created_by, 'faculty_profile'):
                name = self.created_by.faculty_profile.name if self.created_by.faculty_profile else None
            elif self.created_by.user_type == 'officer' and hasattr(self.created_by, 'officer_profile'):
                name = self.created_by.officer_profile.name if self.created_by.officer_profile else None
            elif self.created_by.user_type == 'staff' and hasattr(self.created_by, 'staff_profile'):
                name = self.created_by.staff_profile.name if self.created_by.staff_profile else None
            else:
                # Fallback to full name or email
                name = self.created_by.get_full_name() or self.created_by.email or ''
            
            self.created_by_name = name or email
            self.created_by_email = email
        
        super().save(*args, **kwargs)


class Post(models.Model):
    """
    Model for managing posts (notices, events, seminars, workshops, etc.).
    Can be utilized across multiple apps.
    Only authorized staff (Officer/Faculty) with User Level >= 3 can create posts.
    """
    publish_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Publish Date/Time",
        help_text="Records when the post was issued"
    )
    post_type = models.CharField(
        max_length=20,
        choices=POST_TYPE_CHOICES,
        default='notice',
        verbose_name="Post Type",
        help_text="Category of the post: notice, events, seminars, workshop, or others"
    )
    short_title = models.CharField(
        max_length=20,
        verbose_name="Short Title",
        help_text="Concise, max 20 characters for display (max 4 words)"
    )
    long_title = models.CharField(
        max_length=255,
        verbose_name="Long Title",
        help_text="Detailed headline for the announcement"
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Tags",
        help_text="Comma-separated tags (e.g., 'urgent, closure')"
    )
    description = RichTextField(
        verbose_name="Description",
        help_text="Full body of the announcement"
    )
    is_pinned = models.BooleanField(
        default=False,
        verbose_name="Pin Post",
        help_text="Pin this post to the top of the list"
    )
    created_by = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_posts',
        verbose_name="Created By",
        help_text="Links to the existing authorized user who created the post"
    )
    created_by_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Created By Name",
        help_text="Name of the user who created this post (preserved even if user is deleted)"
    )
    created_by_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Created By Email",
        help_text="Email of the user who created this post (preserved even if user is deleted)"
    )
    thumbnail = models.ImageField(
        upload_to='posts/thumbnails/',
        blank=True,
        null=True,
        verbose_name="Thumbnail Image",
        help_text="Optional thumbnail image (max 1 MB, any aspect ratio)",
        validators=[validate_thumbnail_size]
    )

    class Meta:
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-is_pinned', '-publish_date']

    def __str__(self):
        return f"{self.get_post_type_display()}: {self.short_title} - {self.publish_date.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        """Auto-populate created_by_name and created_by_email when created_by is set, and resize thumbnail"""
        if self.created_by and not self.created_by_name:
            # Get the user's name based on their type
            name = None
            email = self.created_by.email or ''
            
            if self.created_by.user_type == 'faculty' and hasattr(self.created_by, 'faculty_profile'):
                name = self.created_by.faculty_profile.name if self.created_by.faculty_profile else None
            elif self.created_by.user_type == 'officer' and hasattr(self.created_by, 'officer_profile'):
                name = self.created_by.officer_profile.name if self.created_by.officer_profile else None
            elif self.created_by.user_type == 'staff' and hasattr(self.created_by, 'staff_profile'):
                name = self.created_by.staff_profile.name if self.created_by.staff_profile else None
            else:
                # Fallback to full name or email
                name = self.created_by.get_full_name() or self.created_by.email or ''
            
            self.created_by_name = name or email
            self.created_by_email = email
        
        # Resize and compress thumbnail if it exists (maintains aspect ratio)
        if self.thumbnail and hasattr(self.thumbnail, 'file'):
            try:
                # Check if thumbnail is being uploaded/changed
                thumbnail_changed = False
                if self.pk:
                    try:
                        old_post = self.__class__.objects.get(pk=self.pk)
                        thumbnail_changed = old_post.thumbnail != self.thumbnail
                    except self.__class__.DoesNotExist:
                        thumbnail_changed = True
                else:
                    thumbnail_changed = True
                
                if thumbnail_changed:
                    self.thumbnail.file.seek(0)
                    img = Image.open(self.thumbnail)
                    
                    # Convert RGBA/LA/P to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = rgb_img
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Resize maintaining aspect ratio (max 1200px width or 800px height)
                    max_width = 1200
                    max_height = 800
                    width, height = img.size
                    
                    if width > max_width or height > max_height:
                        # Calculate new dimensions maintaining aspect ratio
                        ratio = min(max_width / width, max_height / height)
                        new_width = int(width * ratio)
                        new_height = int(height * ratio)
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Compress to reduce file size (target: under 1MB, optimize quality)
                    buffer = BytesIO()
                    quality = 85
                    img.save(buffer, format='JPEG', optimize=True, quality=quality)
                    
                    # If still too large, reduce quality iteratively
                    max_size_bytes = 1024 * 1024  # 1 MB
                    while buffer.tell() > max_size_bytes and quality > 50:
                        quality -= 5
                        buffer.seek(0)
                        buffer.truncate()
                        img.save(buffer, format='JPEG', optimize=True, quality=quality)
                    
                    # Save the resized and compressed image
                    buffer.seek(0)
                    file_name = self.thumbnail.name.rsplit('.', 1)[0] + '.jpg'
                    self.thumbnail.save(file_name, ContentFile(buffer.read()), save=False)
            except Exception as e:
                # If image processing fails, continue with original image
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to resize thumbnail: {str(e)}")
        
        super().save(*args, **kwargs)

    def clean(self):
        """Validate that short_title has maximum 4 words and max 3 pinned posts"""
        super().clean()
        if self.short_title:
            word_count = len(self.short_title.split())
            if word_count > 4:
                raise ValidationError({
                    'short_title': f'Short title must have maximum 4 words. You entered {word_count} words.'
                })
        
        # Validate maximum 3 pinned posts
        if self.is_pinned:
            # Count other pinned posts (excluding current instance if updating)
            other_pinned = Post.objects.filter(is_pinned=True)
            if self.pk:
                other_pinned = other_pinned.exclude(pk=self.pk)
            
            if other_pinned.count() >= 3:
                raise ValidationError({
                    'is_pinned': 'Maximum 3 posts can be pinned at a time. Please unpin another post first.'
                })
    
    def get_tags_list(self):
        """Helper method to return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []


class PostAttachment(models.Model):
    """
    Model for file attachments linked to posts.
    Supports up to 10 file uploads per post (enforced in forms/views).
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name="Post",
        help_text="Link to the parent post"
    )
    file = models.FileField(
        upload_to='posts/attachments/',
        verbose_name="File",
        help_text="File attachment for the post (PDF only, Max 10MB)"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Uploaded At",
        help_text="Timestamp when the file was uploaded"
    )

    class Meta:
        verbose_name = 'Post Attachment'
        verbose_name_plural = 'Post Attachments'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.post.short_title} - {self.file.name}"


class ClassRoutine(models.Model):
    """
    Model for managing class routines (timetables).
    Only authorized staff (Officer/Faculty) with User Level >= 3 can manage routines.
    """
    academic_year = models.IntegerField(
        verbose_name="Academic Year",
        help_text="The year (e.g., 2025)",
        validators=[
            MinValueValidator(2000),
            MaxValueValidator(datetime.now().year + 5)
        ]
    )
    semester = models.CharField(
        max_length=10,
        choices=SEMESTER_CHOICES,
        verbose_name="Semester",
        help_text="The academic period: Fall or Spring"
    )
    year_semester = models.CharField(
        max_length=3,
        choices=YEAR_SEMESTER_CHOICES,
        verbose_name="Year-Semester",
        help_text="Student level (e.g., 1-1, 2-2, 4-2)"
    )
    section = models.CharField(
        max_length=1,
        choices=SECTION_CHOICES,
        verbose_name="Section",
        help_text="Class division (A to J)"
    )
    routine_image = models.ImageField(
        upload_to='class_routines/',
        verbose_name="Routine Image",
        help_text="The timetable image (Max 1MB, will be compressed and resized to max width 2000px if larger)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
        help_text="Timestamp when the routine was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
        help_text="Timestamp when the routine was last updated"
    )
    created_by = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_routines',
        verbose_name="Created By",
        help_text="Links to the user who created the routine"
    )
    created_by_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Created By Name",
        help_text="Name of the user who created this routine (preserved even if user is deleted)"
    )
    created_by_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Created By Email",
        help_text="Email of the user who created this routine (preserved even if user is deleted)"
    )

    class Meta:
        verbose_name = 'Class Routine'
        verbose_name_plural = 'Class Routines'
        ordering = ['-academic_year', 'semester', 'year_semester', 'section']
        # Ensure unique combination of academic_year, semester, year_semester, and section
        unique_together = ('academic_year', 'semester', 'year_semester', 'section')

    def __str__(self):
        return f"{self.academic_year} {self.semester} - {self.get_year_semester_display()} Section {self.section}"
    
    def save(self, *args, **kwargs):
        """Auto-populate created_by_name and created_by_email when created_by is set"""
        if self.created_by and not self.created_by_name:
            # Get the user's name based on their type
            name = None
            email = self.created_by.email or ''
            
            if self.created_by.user_type == 'faculty' and hasattr(self.created_by, 'faculty_profile'):
                name = self.created_by.faculty_profile.name if self.created_by.faculty_profile else None
            elif self.created_by.user_type == 'officer' and hasattr(self.created_by, 'officer_profile'):
                name = self.created_by.officer_profile.name if self.created_by.officer_profile else None
            elif self.created_by.user_type == 'staff' and hasattr(self.created_by, 'staff_profile'):
                name = self.created_by.staff_profile.name if self.created_by.staff_profile else None
            else:
                # Fallback to full name or email
                name = self.created_by.get_full_name() or self.created_by.email or ''
            
            self.created_by_name = name or email
            self.created_by_email = email
        
        super().save(*args, **kwargs)

    def clean(self):
        """Validate the model"""
        super().clean()
        # Additional validation can be added here if needed


class Gallery(models.Model):
    """
    Simple gallery item managed by power users.
    Each item has a serial number, short title, short description, and an image.
    """
    sl = models.PositiveIntegerField(
        verbose_name="Serial Number (SL)",
        help_text="Controls the display order (lower numbers appear first)."
    )
    short_title = models.CharField(
        max_length=100,
        verbose_name="Short Title",
        help_text="Concise title for the image (e.g., 'Orientation 2025')."
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Short Description",
        help_text="Optional short caption/description (not too big)."
    )
    featured = models.BooleanField(
        default=False,
        verbose_name="Show on Home Page",
        help_text="If checked, this image will appear in the homepage highlight gallery."
    )
    image = models.ImageField(
        upload_to='gallery/',
        verbose_name="Image",
        help_text="Gallery image (will be stored under media/gallery/)."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
        help_text="Timestamp when this gallery item was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
        help_text="Timestamp when this gallery item was last updated."
    )
    created_by = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_gallery_items',
        verbose_name="Created By",
        help_text="Power user who created this gallery item."
    )
    created_by_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Created By Name",
        help_text="Name of the user who created this item (preserved even if user is deleted)."
    )
    created_by_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Created By Email",
        help_text="Email of the user who created this item (preserved even if user is deleted)."
    )

    class Meta:
        verbose_name = 'Gallery Item'
        verbose_name_plural = 'Gallery Items'
        ordering = ['sl', '-created_at']
        unique_together = ('sl', 'short_title')

    def __str__(self):
        return f"{self.sl} - {self.short_title}"

    def save(self, *args, **kwargs):
        """Auto-populate created_by_name and created_by_email when created_by is set."""
        if self.created_by and not self.created_by_name:
            name = None
            email = self.created_by.email or ''

            if self.created_by.user_type == 'faculty' and hasattr(self.created_by, 'faculty_profile'):
                name = self.created_by.faculty_profile.name if self.created_by.faculty_profile else None
            elif self.created_by.user_type == 'officer' and hasattr(self.created_by, 'officer_profile'):
                name = self.created_by.officer_profile.name if self.created_by.officer_profile else None
            elif self.created_by.user_type == 'staff' and hasattr(self.created_by, 'staff_profile'):
                name = self.created_by.staff_profile.name if self.created_by.staff_profile else None
            else:
                # Fallback to full name or email
                name = self.created_by.get_full_name() or self.created_by.email or ''

            self.created_by_name = name or email
            self.created_by_email = email

        # Compress and enforce 16:9 ratio if image exists
        if self.image and hasattr(self.image, 'file'):
            try:
                self.image.file.seek(0)
                img = Image.open(self.image)
                img = img.convert('RGB')

                # Enforce 16:9 aspect ratio by center-cropping if needed
                width, height = img.size
                target_ratio = 16 / 9
                current_ratio = width / height if height else target_ratio

                if current_ratio > target_ratio:
                    # Too wide: crop width
                    new_width = int(height * target_ratio)
                    left = int((width - new_width) / 2)
                    img = img.crop((left, 0, left + new_width, height))
                elif current_ratio < target_ratio:
                    # Too tall: crop height
                    new_height = int(width / target_ratio)
                    top = int((height - new_height) / 2)
                    img = img.crop((0, top, width, top + new_height))

                # Resize to a reasonable max size while keeping 16:9 (optional)
                max_width = 1600
                if img.width > max_width:
                    new_height = int(max_width * 9 / 16)
                    img = img.resize((max_width, new_height), Image.LANCZOS)

                # Compress to <= 600KB
                buffer = BytesIO()
                quality = 85
                img.save(buffer, format='JPEG', optimize=True, quality=quality)

                max_size_bytes = 600 * 1024
                while buffer.tell() > max_size_bytes and quality > 40:
                    quality -= 5
                    buffer.seek(0)
                    buffer.truncate()
                    img.save(buffer, format='JPEG', optimize=True, quality=quality)

                buffer.seek(0)
                file_name = self.image.name.rsplit('.', 1)[0] + '.jpg'
                self.image.save(file_name, ContentFile(buffer.read()), save=False)
            except Exception:
                # If compression fails, just save original
                pass

        super().save(*args, **kwargs)


class ExamRoutine(models.Model):
    """
    Model for managing exam routines.
    Only authorized staff (Officer/Faculty) with User Level >= 3 can manage exam routines.
    """
    academic_year = models.IntegerField(
        verbose_name="Academic Year",
        help_text="The year (e.g., 2025)",
        validators=[
            MinValueValidator(2000),
            MaxValueValidator(datetime.now().year + 5)
        ]
    )
    semester = models.CharField(
        max_length=10,
        choices=SEMESTER_CHOICES,
        verbose_name="Semester",
        help_text="The academic period: Fall or Spring"
    )
    type_of_exam = models.CharField(
        max_length=10,
        choices=EXAM_TYPE_CHOICES,
        verbose_name="Type of Exam",
        help_text="Mid or Final exam"
    )
    year_semester = models.CharField(
        max_length=3,
        choices=YEAR_SEMESTER_CHOICES,
        verbose_name="Year-Semester",
        help_text="Student level (e.g., 1-1, 2-2, 4-2)"
    )
    section = models.CharField(
        max_length=1,
        choices=EXAM_SECTION_CHOICES,
        verbose_name="Section",
        help_text="Class division (A to E)"
    )
    routine_image = models.ImageField(
        upload_to='exam_routines/',
        verbose_name="Routine Image",
        help_text="The exam timetable image (Max 1MB, will be compressed and resized to max width 2000px if larger)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
        help_text="Timestamp when the routine was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
        help_text="Timestamp when the routine was last updated"
    )
    created_by = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_exam_routines',
        verbose_name="Created By",
        help_text="Links to the user who created the routine"
    )
    created_by_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Created By Name",
        help_text="Name of the user who created this routine (preserved even if user is deleted)"
    )
    created_by_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Created By Email",
        help_text="Email of the user who created this routine (preserved even if user is deleted)"
    )

    class Meta:
        verbose_name = 'Exam Routine'
        verbose_name_plural = 'Exam Routines'
        ordering = ['-academic_year', 'semester', 'type_of_exam', 'year_semester', 'section']
        # Ensure unique combination of academic_year, semester, type_of_exam, year_semester, and section
        unique_together = ('academic_year', 'semester', 'type_of_exam', 'year_semester', 'section')

    def __str__(self):
        return f"{self.academic_year} {self.semester} - {self.get_type_of_exam_display()} - {self.get_year_semester_display()} Section {self.section}"
    
    def save(self, *args, **kwargs):
        """Auto-populate created_by_name and created_by_email when created_by is set"""
        if self.created_by and not self.created_by_name:
            # Get the user's name based on their type
            name = None
            email = self.created_by.email or ''
            
            if self.created_by.user_type == 'faculty' and hasattr(self.created_by, 'faculty_profile'):
                name = self.created_by.faculty_profile.name if self.created_by.faculty_profile else None
            elif self.created_by.user_type == 'officer' and hasattr(self.created_by, 'officer_profile'):
                name = self.created_by.officer_profile.name if self.created_by.officer_profile else None
            elif self.created_by.user_type == 'staff' and hasattr(self.created_by, 'staff_profile'):
                name = self.created_by.staff_profile.name if self.created_by.staff_profile else None
            else:
                # Fallback to full name or email
                name = self.created_by.get_full_name() or self.created_by.email or ''
            
            self.created_by_name = name or email
            self.created_by_email = email
        
        super().save(*args, **kwargs)

    def clean(self):
        """Validate the model"""
        super().clean()
        # Additional validation can be added here if needed
