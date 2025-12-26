from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.files.base import ContentFile
from ckeditor.fields import RichTextField
from image_cropping.fields import ImageRatioField, ImageCropField
from PIL import Image
from django.utils import timezone
from django.utils.crypto import get_random_string
import io
import os
import hashlib


class Permission(models.Model):
    """Defines available permissions in the system"""
    CATEGORY_CHOICES = [
        ('office', 'Office'),
        ('clubs', 'Clubs'),
        ('designs', 'Designs'),
        ('users', 'User Management'),
        ('academics', 'Academics'),
    ]
    
    codename = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique permission codename (e.g., 'post_notices')"
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Human-readable permission name"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of what this permission allows"
    )
    
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        blank=True,
        null=True,
        help_text="Permission category for organization"
    )
    
    requires_role = models.JSONField(
        default=list,
        blank=True,
        help_text="List of user_types that can have this permission (empty = any role)"
    )
    
    priority = models.PositiveIntegerField(
        default=100,
        help_text="Display priority (lower = more important)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this permission is currently active"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['category', 'priority', 'name']
        indexes = [
            models.Index(fields=['codename']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.codename})"


class UserPermission(models.Model):
    """Tracks permissions granted to users with full audit trail"""
    user = models.ForeignKey(
        'BaseUser',
        on_delete=models.CASCADE,
        related_name='granted_permissions',
        help_text="User who has this permission"
    )
    
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='user_grants',
        help_text="Permission being granted"
    )
    
    granted_by = models.ForeignKey(
        'BaseUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='permissions_granted',
        help_text="User who granted this permission"
    )
    
    granted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this permission was granted"
    )
    
    revoked_by = models.ForeignKey(
        'BaseUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permissions_revoked',
        help_text="User who revoked this permission"
    )
    
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this permission was revoked"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this permission grant is currently active"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        help_text="Optional notes about why this permission was granted/revoked"
    )
    
    class Meta:
        verbose_name = 'User Permission'
        verbose_name_plural = 'User Permissions'
        ordering = ['-granted_at']
        # Ensure only one active permission grant per user+permission
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'permission'],
                condition=models.Q(is_active=True),
                name='unique_active_user_permission'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['permission', 'is_active']),
            models.Index(fields=['granted_by', 'granted_at']),
        ]
    
    def __str__(self):
        status = "Active" if self.is_active else "Revoked"
        return f"{self.user.email} - {self.permission.name} ({status})"


class AllowedEmail(models.Model):
    USER_TYPE_CHOICES = [
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
        ('officer', 'Officer'),
        ('club_member', 'Club Member'),
    ]
    
    email = models.EmailField(
        unique=True,
        max_length=255,
        help_text="Email address that can sign up"
    )
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        help_text="Type of user this email belongs to"
    )
    
    is_power_user = models.BooleanField(
        default=False,
        help_text="Whether this email should create a power user account (can grant permissions)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Allow this email to sign up (uncheck to prevent new signups)"
    )
    
    is_blocked = models.BooleanField(
        default=False,
        help_text="Block this user from logging in (blocks existing accounts)"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this email was added to allowed list"
    )
    
    created_by = models.ForeignKey(
        'BaseUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_allowed_emails',
        help_text="The user who created this allowed email"
    )
    
    blocked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this email was blocked"
    )
    
    block_reason = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        help_text="Reason for blocking (optional)"
    )
    
    class Meta:
        verbose_name = 'Allowed Email'
        verbose_name_plural = 'Allowed Emails'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email


class BaseUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
        ('officer', 'Officer'),
        ('club_member', 'Club Member'),
    ]
    
    allowed_email = models.OneToOneField(
        AllowedEmail,
        on_delete=models.CASCADE,
        related_name='base_user',
        blank=True,
        null=True,
        help_text="Reference to the allowed email entry (optional for superusers)"
    )
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="Type of user (synced from AllowedEmail, optional for superusers)"
    )
    
    is_power_user = models.BooleanField(
        default=False,
        help_text="Whether this user can grant permissions to other users"
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Contact phone number"
    )
    
    profile_picture = models.ImageField(
        upload_to='user_profiles/',
        blank=True,
        null=True,
        help_text="User profile picture (Max 600KB, will be compressed and resized to 600x600px if larger)"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Account creation date"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update date"
    )
    
    def save(self, *args, **kwargs):
        # Sync user_type and is_power_user from allowed_email if provided
        if self.allowed_email:
            if not self.user_type:
                self.user_type = self.allowed_email.user_type
            if not self.is_power_user:
                self.is_power_user = self.allowed_email.is_power_user
            # Also sync email if not set
            if not self.email:
                self.email = self.allowed_email.email
        super().save(*args, **kwargs)
    
    def has_permission(self, permission_codename):
        """Check if user has a specific permission"""
        # Check if user exists and is active
        if not self or not self.is_active:
            return False
        # Superusers have all permissions
        if self.is_superuser:
            return True
        # Check for granted permission
        return UserPermission.objects.filter(
            user=self,
            permission__codename=permission_codename,
            is_active=True
        ).exists()
    
    def get_all_permissions(self):
        """Get all active permissions for this user"""
        return UserPermission.objects.filter(
            user=self,
            is_active=True
        ).select_related('permission', 'granted_by')
    
    def can_grant_permissions(self):
        """Check if user can grant permissions to others"""
        return self.is_power_user and self.has_permission('manage_user_permissions')
    
    class Meta:
        verbose_name = 'Base User'
        verbose_name_plural = 'Base Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email or self.username


class Faculty(models.Model):
    DESIGNATION_CHOICES = [
        ('Professor', 'Professor'),
        ('Associate Professor', 'Associate Professor'),
        ('Assistant Professor', 'Assistant Professor'),
        ('Lecturer', 'Lecturer'),
        ('Teaching Assistant', 'Teaching Assistant'),
    ]
    
    base_user = models.OneToOneField(
        BaseUser,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='faculty_profile',
        help_text="Base user account"
    )
    
    name = models.CharField(
        max_length=50,
        default="Name",
        help_text="Full name of the faculty member"
    )
    
    shortname = models.CharField(
        max_length=5,
        default='N/A',
        help_text="Short name or initials"
    )
    
    designation = models.CharField(
        max_length=20,
        choices=DESIGNATION_CHOICES,
        null=True,
        blank=True,
        help_text="Academic designation"
    )
    
    phone = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        help_text="Contact phone number"
    )
    
    bio = models.CharField(
        max_length=92,
        blank=True,
        null=True,
        help_text="Short biography (max 92 characters)"
    )
    
    about = RichTextField(
        blank=True,
        null=True,
        help_text="Detailed about section with rich text"
    )
    
    profile_pic = ImageCropField(
        upload_to='faculty_photos/',
        null=True,
        blank=True,
        help_text="Faculty profile picture (Max 600KB, will be compressed and resized to 600x600px if larger)"
    )
    cropping = ImageRatioField(
        'profile_pic',
        '600x600',
        size_warning=True,
        help_text="Crop image to 1:1 aspect ratio (600x600)"
    )
    
    joining_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when faculty joined"
    )
    
    last_office_date = models.DateField(
        null=True,
        blank=True,
        help_text="Last date of service at UAP. If set, faculty will be shown in Legacy Faculty section"
    )
    
    google_scholar_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Google Scholar profile URL"
    )
    
    researchgate_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text="ResearchGate profile URL"
    )
    
    orcid_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text="ORCID profile URL"
    )
    
    scopus_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Scopus profile URL"
    )
    
    linkedin_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text="LinkedIn profile URL"
    )
    
    researches = RichTextField(
        blank=True,
        null=True,
        help_text="Research information with rich text"
    )
    
    citation = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        help_text="Total citations count"
    )
    
    sl = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        blank=True,
        null=True,
        help_text="Serial number for ordering"
    )
    
    routine = RichTextField(
        blank=True,
        null=True,
        help_text="Faculty routine with rich text"
    )
    
    is_head = models.BooleanField(
        default=False,
        null=True,
        blank=True,
        help_text="Whether this faculty member is the head of department"
    )
    
    is_dept_proctor = models.BooleanField(
        default=False,
        null=True,
        blank=True,
        help_text="Whether this faculty member is the department proctor"
    )
    
    is_bsc_admission_coordinator = models.BooleanField(
        default=False,
        null=True,
        blank=True,
        help_text="Whether this faculty member is the BSc admission coordinator"
    )
    
    is_mcse_admission_coordinator = models.BooleanField(
        default=False,
        null=True,
        blank=True,
        help_text="Whether this faculty member is the MCSE admission coordinator"
    )
    
    is_on_study_leave = models.BooleanField(
        default=False,
        null=True,
        blank=True,
        help_text="Whether this faculty member is currently on study leave"
    )
    
    cv = models.FileField(
        upload_to='faculty_cvs/',
        null=True,
        blank=True,
        help_text="Faculty CV/resume document (PDF only, Max 5MB)"
    )
    
    class Meta:
        verbose_name = 'Faculty'
        verbose_name_plural = 'Faculties'
        ordering = ['sl']
    
    def __str__(self):
        return f'{self.sl}. {self.name} | {self.designation or "N/A"}'
    
    def save(self, *args, **kwargs):
        is_update = self.pk is not None
        # Detect if profile_pic file was replaced
        picture_changed = False
        if is_update:
            # Only query if profile_pic might have changed
            # Check update_fields to avoid unnecessary query
            update_fields = kwargs.get('update_fields')
            if update_fields is None or 'profile_pic' in update_fields:
                try:
                    # Use only() to fetch only the field we need (optimization)
                    old = Faculty.objects.only('profile_pic').get(pk=self.pk)
                    old_pic_name = old.profile_pic.name if old.profile_pic else None
                    new_pic_name = self.profile_pic.name if self.profile_pic else None
                    picture_changed = old_pic_name != new_pic_name
                except Faculty.DoesNotExist:
                    picture_changed = False
            # If update_fields is specified and profile_pic is not in it, skip the check
            elif update_fields and 'profile_pic' not in update_fields:
                picture_changed = False
        else:
            picture_changed = bool(self.profile_pic and self.profile_pic.name)
        
        cropping_set = bool(self.profile_pic and self.cropping and self.cropping.strip())
        
        # On first upload (new object), auto-crop to center 1:1
        if not is_update and self.profile_pic and self.profile_pic.name:
            try:
                # Read the image file
                if hasattr(self.profile_pic, 'read'):
                    self.profile_pic.seek(0)
                    image_data = self.profile_pic.read()
                else:
                    image_path = self.profile_pic.path
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                
                # Open image with PIL from bytes
                image = Image.open(io.BytesIO(image_data))
                width, height = image.size
                
                # Calculate center crop for 1:1 ratio
                min_dim = min(width, height)
                left = (width - min_dim) / 2
                top = (height - min_dim) / 2
                right = (width + min_dim) / 2
                bottom = (height + min_dim) / 2
                
                # Crop the image
                cropped_image = image.crop((int(left), int(top), int(right), int(bottom)))
                
                # Resize to exact 600x600
                if cropped_image.size != (600, 600):
                    cropped_image = cropped_image.resize((600, 600), Image.Resampling.LANCZOS)
                
                # Save to memory
                img_io = io.BytesIO()
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
                file_name = os.path.basename(self.profile_pic.name)
                self.profile_pic.save(
                    file_name,
                    ContentFile(img_io.read()),
                    save=False
                )
                
            except Exception as e:
                # If auto-cropping fails, just save normally
                import traceback
                traceback.print_exc()
        
        # On subsequent edits, only crop if:
        # 1. A new picture was uploaded AND cropping coordinates are provided, OR
        # 2. Cropping coordinates are explicitly provided (user wants to crop existing picture)
        elif cropping_set and is_update:
            try:
                # Get the original image path
                if self.profile_pic and self.profile_pic.name:
                    # Read the image file
                    image_data = None
                    
                    # If a new picture was uploaded, read from memory
                    if picture_changed:
                        if hasattr(self.profile_pic, 'read'):
                            try:
                                # Try to read from the file object
                                # Check if file is closed (if attribute exists)
                                if hasattr(self.profile_pic, 'closed') and self.profile_pic.closed:
                                    # File is closed, can't read - clear cropping and skip
                                    self.cropping = ''
                                    super().save(*args, **kwargs)
                                    return
                                # Try to seek and read
                                self.profile_pic.seek(0)
                                image_data = self.profile_pic.read()
                            except (ValueError, OSError, AttributeError, IOError):
                                # File is closed or can't be read, skip cropping
                                self.cropping = ''
                                super().save(*args, **kwargs)
                                return
                    else:
                        # No new picture uploaded, but user wants to crop existing picture
                        # Try to read existing file from disk/storage
                        try:
                            # Try local file path first
                            image_path = self.profile_pic.path
                            if os.path.exists(image_path):
                                with open(image_path, 'rb') as f:
                                    image_data = f.read()
                            else:
                                # File doesn't exist locally, try storage
                                if self.profile_pic.storage.exists(self.profile_pic.name):
                                    with self.profile_pic.storage.open(self.profile_pic.name, 'rb') as f:
                                        image_data = f.read()
                                else:
                                    # File doesn't exist, skip cropping and clear cropping field
                                    self.cropping = ''
                                    super().save(*args, **kwargs)
                                    return
                        except (ValueError, AttributeError, IOError, OSError):
                            # Can't access file, skip cropping
                            self.cropping = ''
                            super().save(*args, **kwargs)
                            return
                    
                    if image_data:
                        # Open image with PIL from bytes
                        image = Image.open(io.BytesIO(image_data))
                        
                        # Parse cropping coordinates (format: "x1,y1,x2,y2")
                        try:
                            crop_coords = [int(x.strip()) for x in self.cropping.split(',')]
                            if len(crop_coords) == 4:
                                x1, y1, x2, y2 = crop_coords
                                
                                # Crop the image
                                cropped_image = image.crop((x1, y1, x2, y2))
                                
                                # Resize to exact 600x600 if needed
                                if cropped_image.size != (600, 600):
                                    cropped_image = cropped_image.resize((600, 600), Image.Resampling.LANCZOS)
                                
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
                                file_name = os.path.basename(self.profile_pic.name)
                                self.profile_pic.save(
                                    file_name,
                                    ContentFile(img_io.read()),
                                    save=False
                                )
                                
                                # Clear cropping coordinates after applying
                                self.cropping = ''
                        except (ValueError, IndexError):
                            # Invalid cropping coordinates, clear them
                            self.cropping = ''
                    else:
                        # No image data available, clear cropping field
                        self.cropping = ''
                else:
                    # No profile picture, clear cropping field
                    self.cropping = ''
            except Exception as e:
                # If cropping fails for any reason, clear cropping field and save normally
                self.cropping = ''
                import traceback
                traceback.print_exc()
        elif is_update and self.cropping and self.cropping.strip() and not picture_changed:
            # If cropping coordinates exist but no picture available, clear cropping
            if not self.profile_pic or not self.profile_pic.name:
                self.cropping = ''
        
        super().save(*args, **kwargs)


class Publication(models.Model):
    """Model to store faculty publications"""
    TYPE_CHOICES = [
        ('journal', 'Journal'),
        ('conf', 'Conference'),
        ('bookchapter', 'Book Chapter'),
        ('other', 'Other'),
    ]
    
    RANKING_CHOICES = [
        ('q1', 'Q1'),
        ('q2', 'Q2'),
        ('q3', 'Q3'),
        ('q4', 'Q4'),
        ('a1', 'A1'),
        ('a2', 'A2'),
        ('a3', 'A3'),
        ('a4', 'A4'),
        ('not_indexed', 'Not Indexed'),
    ]
    
    title = models.CharField(
        max_length=500,
        help_text="Publication title"
    )
    
    pub_year = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
        help_text="Publication year"
    )
    
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="Type of publication"
    )
    
    ranking = models.CharField(
        max_length=20,
        choices=RANKING_CHOICES,
        help_text="Journal/Conference ranking"
    )
    
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name='publications',
        help_text="Faculty member who authored this publication"
    )
    
    # Optional fields
    link = models.URLField(
        blank=True,
        null=True,
        help_text="Link to the publication"
    )
    
    doi = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Digital Object Identifier (DOI)"
    )
    
    published_at = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Journal/Conference/Venue name"
    )
    
    contribution = models.TextField(
        blank=True,
        null=True,
        help_text="Author's contribution to the publication"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this publication was added to the system"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this publication was last updated"
    )
    
    class Meta:
        verbose_name = 'Publication'
        verbose_name_plural = 'Publications'
        ordering = ['-pub_year', 'title']
        indexes = [
            models.Index(fields=['faculty']),
            models.Index(fields=['pub_year']),
            models.Index(fields=['ranking']),
            models.Index(fields=['faculty', 'pub_year']),
        ]
    
    def __str__(self):
        return f'{self.title} - {self.faculty.name} ({self.pub_year})'


class Staff(models.Model):
    DESIGNATION_CHOICES = [
        ('Lab Assistant', 'Lab Assistant'),
        ('Lab Attendant', 'Lab Attendant'),
    ]
    
    base_user = models.OneToOneField(
        BaseUser,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='staff_profile',
        help_text="Base user account"
    )
    
    name = models.CharField(
        max_length=100,
        help_text="Full name of the staff member"
    )
    
    designation = models.CharField(
        max_length=20,
        choices=DESIGNATION_CHOICES,
        help_text="Staff designation"
    )
    
    phone = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        help_text="Contact phone number"
    )
    
    bio = models.TextField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Short biography"
    )
    
    profile_pic = models.ImageField(
        upload_to='staff_photos/',
        null=True,
        blank=True,
        help_text="Staff profile picture (Max 300KB, will be compressed and resized to 400x400px if larger)"
    )
    
    joining_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when staff joined"
    )
    
    sl = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Serial number for ordering"
    )
    
    lab_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Lab number or identifier"
    )
    
    lab_address = models.TextField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Lab address or location"
    )
    
    class Meta:
        verbose_name = 'Staff'
        verbose_name_plural = 'Staff'
        ordering = ['sl']
    
    def __str__(self):
        return f'{self.sl}. {self.name} | {self.designation}'


class Officer(models.Model):
    base_user = models.OneToOneField(
        BaseUser,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='officer_profile',
        help_text="Base user account"
    )
    
    name = models.CharField(
        max_length=100,
        help_text="Full name of the officer"
    )
    
    position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Official position or title"
    )
    
    phone = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        help_text="Contact phone number"
    )
    
    bio = models.TextField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Short biography"
    )
    
    profile_pic = models.ImageField(
        upload_to='officer_photos/',
        null=True,
        blank=True,
        help_text="Officer profile picture (Max 300KB, will be compressed and resized to 400x400px if larger)"
    )
    
    joining_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when officer joined"
    )
    
    sl = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Serial number for ordering"
    )
    
    about = RichTextField(
        blank=True,
        null=True,
        help_text="Detailed about section with rich text"
    )
    
    class Meta:
        verbose_name = 'Officer'
        verbose_name_plural = 'Officers'
        ordering = ['sl']
    
    def __str__(self):
        return f'{self.sl}. {self.name} | {self.position or "N/A"}'


class ClubMember(models.Model):
    base_user = models.OneToOneField(
        BaseUser,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='club_member_profile',
        help_text="Base user account"
    )
    
    name = models.CharField(
        max_length=100,
        help_text="Full name of the club member"
    )
    
    student_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Student ID number"
    )
    
    about = RichTextField(
        blank=True,
        null=True,
        help_text="About the club member with rich text"
    )
    
    profile_pic = models.ImageField(
        upload_to='club_member_photos/',
        null=True,
        blank=True,
        help_text="Club member profile picture (Max 300KB, will be compressed and resized to 400x400px if larger)"
    )
    
    last_club_position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Last position held in the club"
    )
    
    class Meta:
        verbose_name = 'Club Member'
        verbose_name_plural = 'Club Members'
        ordering = ['name']
    
    def __str__(self):
        return f'{self.name} | {self.student_id}'


class PasswordResetToken(models.Model):
    """Model to store password reset tokens"""
    user = models.ForeignKey(
        BaseUser,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        help_text="Unique token for password reset"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the token was created"
    )
    expires_at = models.DateTimeField(
        help_text="When the token expires"
    )
    used = models.BooleanField(
        default=False,
        help_text="Whether this token has been used"
    )
    
    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'used']),
        ]
    
    def __str__(self):
        return f'Token for {self.user.email} - {"Used" if self.used else "Active"}'

    def is_valid(self):
        """Check if token is valid (not used and not expired)"""
        return (
                not self.used and
                timezone.now() <= self.expires_at
        )

    @classmethod
    def generate_token(cls, user, hours=24):
        """Generate a new password reset token for a user"""
        # Mark old tokens as used (DO NOT delete)
        cls.objects.filter(user=user, used=False).update(used=True)

        # Generate raw token and hash it
        raw_token = get_random_string(48)
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = timezone.now() + timezone.timedelta(hours=hours)

        cls.objects.create(
            user=user,
            token=hashed_token,
            expires_at=expires_at
        )

        # Return the raw token for sending via email
        return raw_token


class Contributor(models.Model):
    """Model to store project contributors and their contributions"""
    PROJECT_TYPE_CHOICES = [
        ('final', 'Final Development & Deployment'),
        ('course', 'Course-Based Development'),
    ]
    
    name = models.CharField(
        max_length=255,
        help_text="Full name of the contributor"
    )
    
    student_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Student ID (nullable)"
    )
    
    github_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="GitHub username (nullable)"
    )
    
    role = models.CharField(
        max_length=255,
        help_text="Contributor's role in the project"
    )
    
    reflection = models.TextField(
        blank=True,
        null=True,
        help_text="Optional reflection text from the contributor"
    )
    
    portfolio_link = models.URLField(
        blank=True,
        null=True,
        help_text="Portfolio or personal website URL"
    )
    
    photo = models.ImageField(
        upload_to='contributor_photos/',
        blank=True,
        null=True,
        help_text="Profile photo of the contributor (Max 300KB, will be compressed and resized to 400x400px if larger)"
    )
    
    project_type = models.CharField(
        max_length=20,
        choices=PROJECT_TYPE_CHOICES,
        help_text="Type of project contribution"
    )
    
    order = models.PositiveIntegerField(
        default=0,
        help_text="Order for custom sorting within each project_type"
    )
    
    lines_added = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Number of lines added (contribution metric)"
    )
    
    lines_deleted = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Number of lines deleted (contribution metric)"
    )
    
    number_of_commits = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Number of commits (contribution metric)"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this contributor was added"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update date"
    )
    
    class Meta:
        verbose_name = 'Contributor'
        verbose_name_plural = 'Contributors'
        ordering = ['project_type', 'order', 'name']
    
    def __str__(self):
        return f'{self.name} - {self.get_project_type_display()}'
