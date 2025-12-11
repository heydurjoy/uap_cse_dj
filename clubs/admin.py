from django.contrib import admin
from image_cropping import ImageCroppingMixin
from .models import Club, ClubPosition, ClubPost, ClubPosition


def check_club_access(user):
    """Check if user has access level 4+ and is Faculty or Officer"""
    if not user.is_authenticated:
        return False
    try:
        access_level = int(user.access_level) if user.access_level else 0
        if access_level < 4:
            return False
        # Check if user is Faculty or Officer
        user_type = user.user_type
        return user_type and user_type in ['faculty', 'officer']
    except (ValueError, TypeError):
        return False


@admin.register(Club)
class ClubAdmin(ImageCroppingMixin, admin.ModelAdmin):
    list_display = ['sl', 'name', 'convener', 'president', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'moto', 'description']
    ordering = ['sl', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('sl', 'name', 'short_name', 'moto', 'description')
        }),
        ('Personnel', {
            'fields': ('convener', 'president')
        }),
        ('Logo', {
            'fields': ('logo', 'logo_cropping')
        }),
        ('Cover Photo', {
            'fields': ('cover_photo', 'cover_photo_cropping')
        }),
        ('Social Links', {
            'fields': ('website_url', 'facebook_url', 'instagram_url', 'youtube_url')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def has_view_permission(self, request, obj=None):
        """Only level 4+ Faculty or Officers can view clubs"""
        return check_club_access(request.user)
    
    def has_add_permission(self, request):
        """Only level 4+ Faculty or Officers can add clubs"""
        return check_club_access(request.user)
    
    def has_change_permission(self, request, obj=None):
        """Only level 4+ Faculty or Officers can change clubs"""
        return check_club_access(request.user)
    
    def has_delete_permission(self, request, obj=None):
        """Only level 4+ Faculty or Officers can delete clubs"""
        return check_club_access(request.user)


@admin.register(ClubPosition)
class ClubPositionAdmin(admin.ModelAdmin):
    list_display = ['club', 'position_title', 'academic_year', 'semester', 'get_person_name', 'get_person_type']
    list_filter = ['academic_year', 'semester', 'club']
    search_fields = ['position_title', 'club__name']
    ordering = ['-academic_year', 'semester', 'position_title']
    
    def get_person_name(self, obj):
        return obj.get_person_name()
    get_person_name.short_description = 'Person'
    
    def get_person_type(self, obj):
        return obj.get_person_type()
    get_person_type.short_description = 'Type'


@admin.register(ClubPost)
class ClubPostAdmin(admin.ModelAdmin):
    list_display = ['club', 'short_title', 'post_type', 'is_pinned', 'posted_by', 'created_at']
    list_filter = ['post_type', 'is_pinned', 'created_at', 'club']
    search_fields = ['short_title', 'long_title', 'tags', 'description', 'club__name']
    ordering = ['-is_pinned', '-created_at']
    readonly_fields = ['created_at', 'last_edited_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('club', 'post_type', 'short_title', 'long_title', 'tags', 'is_pinned')
        }),
        ('Content', {
            'fields': ('description',)
        }),
        ('Event Details', {
            'fields': ('start_date_time', 'end_date_time'),
            'classes': ('collapse',)
        }),
        ('Audit Trail', {
            'fields': ('posted_by', 'created_at', 'last_edited_by', 'last_edited_at')
        }),
    )
