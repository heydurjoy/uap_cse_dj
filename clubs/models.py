from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField
from image_cropping.fields import ImageRatioField, ImageCropField
from datetime import datetime

# Semester Choices
SEMESTER_CHOICES = (
    ('Fall', 'Fall'),
    ('Spring', 'Spring'),
)


class Club(models.Model):
    """
    The main entity representing an academic or social club.
    Mandatory field: name. All others are optional (nullable).
    """
    
    # --- Mandatory Field ---
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The official, unique name of the club"
    )
    
    # --- Short Name (Optional) ---
    short_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Short name or abbreviation for the club"
    )
    
    # --- Serial Number (Optional) ---
    sl = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        blank=True,
        null=True,
        help_text="Serial number for ordering"
    )
    
    # --- Descriptive Fields (Optional) ---
    moto = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The club's motto or slogan"
    )
    
    description = RichTextField(
        blank=True,
        null=True,
        help_text="Detailed information about the club's goals and activities"
    )
    
    # --- Personnel (Optional) ---
    convener = models.ForeignKey(
        'people.Faculty', 
        on_delete=models.SET_NULL,
        related_name='convened_clubs',
        null=True,
        blank=True,
        help_text="The faculty member advising the club (optional)"
    )

    # --- President (Optional ClubMember object) ---
    president = models.ForeignKey(
        'people.ClubMember', 
        on_delete=models.SET_NULL,
        related_name='led_clubs',
        null=True,
        blank=True,
        help_text="The club member designated as the current President (optional)"
    )
    
    # --- Media Fields (Cropable and Optional) ---
    
    # Logo (1:1 Ratio)
    logo = ImageCropField(
        upload_to='club_assets/logos/',
        null=True,
        blank=True,
        help_text="Small club logo"
    )
    logo_cropping = ImageRatioField(
        'logo', 
        '400x400', 
        size_warning=True, 
        help_text="Crop to 1:1 aspect ratio"
    )

    # Cover Photo (21:6 Ratio)
    cover_photo = ImageCropField(
        upload_to='club_assets/covers/',
        null=True,
        blank=True,
        help_text="Large banner image for the club's profile"
    )
    cover_photo_cropping = ImageRatioField(
        'cover_photo',
        '2100x600',  # CRITICAL: Enforces the 21:6 ratio
        size_warning=True,
        help_text="Crop to the 21:6 aspect ratio"
    )
    
    # --- Link Fields (Optional) ---
    website_url = models.URLField(max_length=255, blank=True, null=True, help_text="Official club website URL")
    facebook_url = models.URLField(max_length=255, blank=True, null=True, help_text="Facebook page URL")
    instagram_url = models.URLField(max_length=255, blank=True, null=True, help_text="Instagram profile URL")
    youtube_url = models.URLField(max_length=255, blank=True, null=True, help_text="YouTube channel URL")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Club'
        verbose_name_plural = 'Clubs'
        ordering = ['sl', 'name']
        
    def __str__(self):
        if self.sl:
            return f'{self.sl}. {self.name}'
        return self.name


class ClubPosition(models.Model):
    """
    Model to track positions (faculty or club members) in clubs for specific semesters.
    Allows conveners to assign people to positions for specific academic years and semesters.
    """
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='positions',
        help_text="The club this position belongs to"
    )
    
    sl = models.PositiveIntegerField(
        default=1,
        help_text="Serial number for ordering within the club (used for sorting, not displayed)"
    )
    
    position_title = models.CharField(
        max_length=100,
        help_text="Title of the position (e.g., Vice President, Secretary, Treasurer)"
    )
    
    academic_year = models.SmallIntegerField(
        help_text="Academic year (e.g., 2024)",
        validators=[MinValueValidator(2000)]
    )
    
    semester = models.CharField(
        max_length=10,
        choices=SEMESTER_CHOICES,
        help_text="Semester: Fall or Spring"
    )
    
    # Can be either Faculty or ClubMember
    faculty = models.ForeignKey(
        'people.Faculty',
        on_delete=models.CASCADE,
        related_name='club_positions',
        null=True,
        blank=True,
        help_text="Faculty member in this position (if applicable)"
    )
    
    club_member = models.ForeignKey(
        'people.ClubMember',
        on_delete=models.CASCADE,
        related_name='club_positions',
        null=True,
        blank=True,
        help_text="Club member in this position (if applicable)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Club Position'
        verbose_name_plural = 'Club Positions'
        ordering = ['-academic_year', 'semester', 'sl', 'position_title']
        # Ensure one person per position per semester
        unique_together = [
            ('club', 'position_title', 'academic_year', 'semester', 'faculty'),
            ('club', 'position_title', 'academic_year', 'semester', 'club_member'),
        ]
    
    def clean(self):
        """Ensure either faculty or club_member is set, but not both"""
        if not self.faculty and not self.club_member:
            raise ValidationError('Either faculty or club_member must be set.')
        if self.faculty and self.club_member:
            raise ValidationError('Cannot set both faculty and club_member.')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_person_name(self):
        """Get the name of the person in this position"""
        if self.faculty:
            return self.faculty.name
        elif self.club_member:
            return self.club_member.name
        return "Not assigned"
    
    def get_person_type(self):
        """Get the type of person (faculty or club_member)"""
        if self.faculty:
            return 'faculty'
        elif self.club_member:
            return 'club_member'
        return None
    
    def __str__(self):
        person = self.get_person_name()
        return f"{self.club.name} - {self.position_title} ({self.academic_year} {self.semester}): {person}"


# Club Post Type Choices
CLUB_POST_TYPE_CHOICES = (
    ('event', 'Event'),
    ('seminar', 'Seminar'),
    ('contest', 'Contest'),
    ('workshop', 'Workshop'),
    ('training', 'Training'),
    ('other', 'Other'),
)


class ClubPost(models.Model):
    """
    Model for club posts/announcements.
    Club members can create posts for their clubs.
    """
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='posts',
        help_text="The club this post belongs to"
    )
    
    post_type = models.CharField(
        max_length=20,
        choices=CLUB_POST_TYPE_CHOICES,
        default='event',
        help_text="Category of the post: Event, Seminar, Contest, Workshop, Training, or Other"
    )
    
    short_title = models.CharField(
        max_length=50,
        help_text="Short, display title (max 50 characters)"
    )
    
    long_title = models.CharField(
        max_length=255,
        help_text="Detailed headline for the announcement"
    )
    
    tags = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Comma-separated tags (e.g., 'signup, deadline')"
    )
    
    description = RichTextField(
        help_text="Main body content with rich text formatting"
    )
    
    start_date_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional start date/time for events/workshops"
    )
    
    end_date_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional end date/time for event duration"
    )
    
    posted_by = models.ForeignKey(
        'people.BaseUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='posted_club_posts',
        help_text="The original user who created this post"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Records creation time"
    )
    
    last_edited_by = models.ForeignKey(
        'people.BaseUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_edited_club_posts',
        help_text="The last user who saved/edited this post"
    )
    
    last_edited_at = models.DateTimeField(
        auto_now=True,
        help_text="Records last modification time"
    )
    
    is_pinned = models.BooleanField(
        default=False,
        help_text="Pin this post to the top (max 3 per club)"
    )
    
    class Meta:
        verbose_name = 'Club Post'
        verbose_name_plural = 'Club Posts'
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return f"{self.club.name} - {self.short_title}"
    
    def get_tags_list(self):
        """Helper method to return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
