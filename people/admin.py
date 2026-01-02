from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from image_cropping import ImageCroppingMixin
from .models import (
    AllowedEmail, BaseUser, Faculty, Staff, Officer, ClubMember, 
    PasswordResetToken, Permission, UserPermission, Contributor, Publication
)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename', 'category', 'is_active', 'priority']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'codename', 'description']
    list_editable = ['is_active', 'priority']
    readonly_fields = ['created_at']
    ordering = ['category', 'priority', 'name']
    
    fieldsets = (
        ('Permission Information', {
            'fields': ('codename', 'name', 'description', 'category')
        }),
        ('Access Control', {
            'fields': ('requires_role', 'priority', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'permission', 'is_active', 'granted_by', 'granted_at', 'revoked_at']
    list_filter = ['is_active', 'permission__category', 'granted_at', 'revoked_at']
    search_fields = ['user__email', 'user__username', 'permission__name', 'permission__codename']
    readonly_fields = ['granted_at', 'revoked_at']
    ordering = ['-granted_at']
    
    fieldsets = (
        ('Permission Grant', {
            'fields': ('user', 'permission', 'is_active')
        }),
        ('Audit Trail', {
            'fields': ('granted_by', 'granted_at', 'revoked_by', 'revoked_at', 'notes')
        }),
    )


@admin.register(AllowedEmail)
class AllowedEmailAdmin(admin.ModelAdmin):
    list_display = ['email', 'user_type', 'is_power_user', 'is_active', 'is_blocked', 'created_at']
    list_filter = ['user_type', 'is_power_user', 'is_active', 'is_blocked', 'created_at']
    search_fields = ['email']
    list_editable = ['is_active', 'is_blocked', 'is_power_user']
    readonly_fields = ['created_at', 'blocked_at']
    
    fieldsets = (
        ('Email Information', {
            'fields': ('email', 'user_type', 'is_power_user')
        }),
        ('Access Control', {
            'fields': ('is_active', 'is_blocked', 'blocked_at', 'block_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    actions = ['block_emails', 'unblock_emails', 'activate_emails', 'deactivate_emails']
    
    def block_emails(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_blocked=True, blocked_at=timezone.now())
        self.message_user(request, f'{updated} email(s) blocked.')
    block_emails.short_description = "Block selected emails"
    
    def unblock_emails(self, request, queryset):
        updated = queryset.update(is_blocked=False, blocked_at=None)
        self.message_user(request, f'{updated} email(s) unblocked.')
    unblock_emails.short_description = "Unblock selected emails"
    
    def activate_emails(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} email(s) activated for signup.')
    activate_emails.short_description = "Activate selected emails for signup"
    
    def deactivate_emails(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} email(s) deactivated for signup.')
    deactivate_emails.short_description = "Deactivate selected emails for signup"


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'expires_at', 'used', 'is_valid_display']
    list_filter = ['used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'user__username', 'token']
    readonly_fields = ['token', 'created_at', 'expires_at']
    ordering = ['-created_at']
    
    def is_valid_display(self, obj):
        return obj.is_valid()
    is_valid_display.boolean = True
    is_valid_display.short_description = 'Valid'


@admin.register(BaseUser)
class BaseUserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'user_type', 'is_power_user', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_power_user', 'is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    readonly_fields = ['created_at', 'updated_at', 'date_joined', 'last_login']
    # Keep Django's built-in user_permissions in filter_horizontal (from parent class)
    # Our custom permissions are managed via UserPermission model
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('allowed_email', 'user_type', 'is_power_user', 'phone_number', 'profile_picture')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': ('allowed_email', 'user_type', 'is_power_user', 'phone_number', 'profile_picture')
        }),
    )


class PublicationInline(admin.TabularInline):
    """Inline admin for publications in Faculty admin"""
    model = Publication
    extra = 1
    fields = ('title', 'pub_year', 'type', 'ranking', 'published_at', 'doi', 'link')
    verbose_name = 'Publication'
    verbose_name_plural = 'Publications'


@admin.register(Faculty)
class FacultyAdmin(ImageCroppingMixin, admin.ModelAdmin):
    list_display = ['name', 'designation', 'sl', 'base_user', 'citation']
    list_filter = ['designation', 'joining_date']
    search_fields = ['name', 'shortname', 'base_user__email']
    ordering = ['sl']
    inlines = [PublicationInline]
    
    fieldsets = (
        ('Base User', {
            'fields': ('base_user',)
        }),
        ('Basic Information', {
            'fields': ('name', 'shortname', 'designation', 'phone', 'sl')
        }),
        ('Profile', {
            'fields': ('profile_pic', 'cropping', 'bio', 'about', 'joining_date')
        }),
        ('Research Links', {
            'fields': ('google_scholar_url', 'researchgate_url', 'orcid_url', 'scopus_url', 'linkedin_url')
        }),
        ('Research Information', {
            'fields': ('researches', 'citation')
        }),
        ('Routine', {
            'fields': ('routine',)
        }),
        ('Roles & Status', {
            'fields': ('is_head', 'is_dept_proctor', 'is_bsc_admission_coordinator', 'is_mcse_admission_coordinator', 'is_on_study_leave', 'is_inter_departmental', 'is_visiting', 'last_office_date')
        }),
        ('Qualifications', {
            'fields': ('is_phd', 'is_masters', 'educational_qualification', 'course_conducted')
        }),
        ('Documents', {
            'fields': ('cv',)
        }),
    )


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['name', 'designation', 'sl', 'base_user', 'lab_number']
    list_filter = ['designation', 'joining_date']
    search_fields = ['name', 'base_user__email', 'lab_number']
    ordering = ['sl']
    
    fieldsets = (
        ('Base User', {
            'fields': ('base_user',)
        }),
        ('Basic Information', {
            'fields': ('name', 'designation', 'phone', 'sl')
        }),
        ('Profile', {
            'fields': ('profile_pic', 'bio', 'joining_date')
        }),
        ('Lab Information', {
            'fields': ('lab_number', 'lab_address')
        }),
    )


@admin.register(Officer)
class OfficerAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'sl', 'base_user']
    list_filter = ['joining_date']
    search_fields = ['name', 'position', 'base_user__email']
    ordering = ['sl']
    
    fieldsets = (
        ('Base User', {
            'fields': ('base_user',)
        }),
        ('Basic Information', {
            'fields': ('name', 'position', 'phone', 'sl')
        }),
        ('Profile', {
            'fields': ('profile_pic', 'bio', 'about', 'joining_date')
        }),
    )


@admin.register(ClubMember)
class ClubMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'student_id', 'last_club_position', 'base_user']
    search_fields = ['name', 'student_id', 'base_user__email', 'last_club_position']
    ordering = ['name']
    
    fieldsets = (
        ('Base User', {
            'fields': ('base_user',)
        }),
        ('Basic Information', {
            'fields': ('name', 'student_id', 'last_club_position')
        }),
        ('Profile', {
            'fields': ('profile_pic', 'about')
        }),
    )


@admin.register(Contributor)
class ContributorAdmin(admin.ModelAdmin):
    list_display = ['name', 'student_id', 'github_username', 'role', 'project_type', 'order', 'number_of_commits', 'lines_added']
    list_filter = ['project_type', 'created_at']
    search_fields = ['name', 'student_id', 'github_username', 'role']
    list_editable = ['order']
    ordering = ['project_type', 'order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'student_id', 'github_username', 'role', 'reflection')
        }),
        ('Project Info', {
            'fields': ('project_type', 'order')
        }),
        ('Contribution Metrics', {
            'fields': ('lines_added', 'lines_deleted', 'number_of_commits')
        }),
        ('Profile', {
            'fields': ('photo', 'portfolio_link')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ['title', 'faculty', 'pub_year', 'type', 'ranking', 'published_at']
    list_filter = ['type', 'ranking', 'pub_year']
    search_fields = ['title', 'faculty__name', 'doi', 'published_at']
    ordering = ['-pub_year', 'title']
    raw_id_fields = ['faculty']
    
    fieldsets = (
        ('Publication Information', {
            'fields': ('title', 'faculty', 'pub_year', 'type', 'ranking')
        }),
        ('Publication Details', {
            'fields': ('published_at', 'doi', 'link', 'contribution')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
