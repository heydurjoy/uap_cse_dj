from django.contrib import admin
from .models import AdmissionResult, Post, PostAttachment, ClassRoutine, ExamRoutine, Gallery


@admin.register(AdmissionResult)
class AdmissionResultAdmin(admin.ModelAdmin):
    list_display = ['academic_year', 'semester', 'slot', 'publish_date', 'created_by']
    list_filter = ['academic_year', 'semester', 'publish_date']
    search_fields = ['academic_year', 'semester', 'slot', 'result_content']
    ordering = ['-publish_date', '-academic_year', 'semester', 'slot']
    readonly_fields = ['publish_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('academic_year', 'semester', 'slot', 'publish_date')
        }),
        ('Content', {
            'fields': ('result_content', 'official_pdf')
        }),
        ('Metadata', {
            'fields': ('created_by',)
        }),
    )


class PostAttachmentInline(admin.TabularInline):
    """Inline admin for Post Attachments"""
    model = PostAttachment
    extra = 1
    max_num = 10  # Enforce max 10 attachments in admin
    fields = ('file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['short_title', 'post_type', 'long_title', 'is_pinned', 'publish_date', 'created_by']
    list_filter = ['post_type', 'is_pinned', 'publish_date', 'created_by']
    search_fields = ['short_title', 'long_title', 'tags', 'description']
    ordering = ['-is_pinned', '-publish_date']
    readonly_fields = ['publish_date']
    list_editable = ['is_pinned']  # Allow quick editing of pin status
    inlines = [PostAttachmentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('post_type', 'short_title', 'long_title', 'publish_date', 'is_pinned')
        }),
        ('Content', {
            'fields': ('thumbnail', 'tags', 'description')
        }),
        ('Metadata', {
            'fields': ('created_by',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Override save to handle max 3 pinned posts - automatically unpin oldest if needed"""
        if obj.is_pinned:
            # Count other pinned posts (excluding current instance if updating)
            other_pinned = Post.objects.filter(is_pinned=True)
            if obj.pk:
                other_pinned = other_pinned.exclude(pk=obj.pk)
            
            if other_pinned.count() >= 3:
                # Find and unpin the oldest pinned post
                oldest_pinned = other_pinned.order_by('publish_date').first()
                if oldest_pinned:
                    oldest_pinned.is_pinned = False
                    oldest_pinned.save()
                    from django.contrib import messages
                    messages.info(request, f'Automatically unpinned the oldest pinned post: "{oldest_pinned.short_title}" to make room for this post.')
        
        super().save_model(request, obj, form, change)


@admin.register(PostAttachment)
class PostAttachmentAdmin(admin.ModelAdmin):
    list_display = ['post', 'file', 'uploaded_at']
    list_filter = ['uploaded_at', 'post__post_type', 'post']
    search_fields = ['post__short_title', 'post__long_title', 'file']
    ordering = ['-uploaded_at']
    readonly_fields = ['uploaded_at']
    
    fieldsets = (
        ('File Information', {
            'fields': ('post', 'file', 'uploaded_at')
        }),
    )


@admin.register(ClassRoutine)
class ClassRoutineAdmin(admin.ModelAdmin):
    list_display = ['academic_year', 'semester', 'year_semester', 'section', 'created_at', 'created_by']
    list_filter = ['academic_year', 'semester', 'year_semester', 'section', 'created_at']
    search_fields = ['academic_year', 'semester', 'year_semester', 'section']
    ordering = ['-academic_year', 'semester', 'year_semester', 'section']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Routine Information', {
            'fields': ('academic_year', 'semester', 'year_semester', 'section')
        }),
        ('Routine Image', {
            'fields': ('routine_image',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(ExamRoutine)
class ExamRoutineAdmin(admin.ModelAdmin):
    list_display = ['academic_year', 'semester', 'type_of_exam', 'year_semester', 'section', 'created_at', 'created_by']
    list_filter = ['academic_year', 'semester', 'type_of_exam', 'year_semester', 'section', 'created_at']
    search_fields = ['academic_year', 'semester', 'type_of_exam', 'year_semester', 'section']
    ordering = ['-academic_year', 'semester', 'type_of_exam', 'year_semester', 'section']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Routine Information', {
            'fields': ('academic_year', 'semester', 'type_of_exam', 'year_semester', 'section')
        }),
        ('Routine Image', {
            'fields': ('routine_image',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['sl', 'short_title', 'created_at', 'created_by']
    list_filter = ['created_at']
    search_fields = ['short_title', 'description', 'created_by_name', 'created_by_email']
    ordering = ['sl', '-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Gallery Item', {
            'fields': ('sl', 'short_title', 'description', 'image')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
