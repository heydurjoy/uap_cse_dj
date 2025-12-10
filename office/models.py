from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from ckeditor.fields import RichTextField
from people.models import BaseUser
from datetime import datetime


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
        help_text="Single file for the official, signed result document"
    )
    created_by = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_admission_results',
        verbose_name="Created By",
        help_text="Links to the existing authorized user who created the post"
    )

    class Meta:
        verbose_name = 'Admission Result'
        verbose_name_plural = 'Admission Results'
        ordering = ['-publish_date', '-academic_year', 'semester', 'slot']
        # Ensure unique combination of academic_year, semester, and slot
        unique_together = ('academic_year', 'semester', 'slot')

    def __str__(self):
        return f"{self.academic_year} {self.semester} - Slot {self.slot}"


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

    class Meta:
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-is_pinned', '-publish_date']

    def __str__(self):
        return f"{self.get_post_type_display()}: {self.short_title} - {self.publish_date.strftime('%Y-%m-%d')}"

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
        help_text="File attachment for the post"
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
        help_text="The timetable image"
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

    class Meta:
        verbose_name = 'Class Routine'
        verbose_name_plural = 'Class Routines'
        ordering = ['-academic_year', 'semester', 'year_semester', 'section']
        # Ensure unique combination of academic_year, semester, year_semester, and section
        unique_together = ('academic_year', 'semester', 'year_semester', 'section')

    def __str__(self):
        return f"{self.academic_year} {self.semester} - {self.get_year_semester_display()} Section {self.section}"

    def clean(self):
        """Validate the model"""
        super().clean()
        # Additional validation can be added here if needed
