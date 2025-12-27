from django.contrib import admin
from image_cropping import ImageCroppingMixin
from .models import FeatureCard, HeroTags, AdmissionElement, AcademicCalendar, Curricula


@admin.register(FeatureCard)
class FeatureCardAdmin(ImageCroppingMixin, admin.ModelAdmin):
    list_display = ['sl_number', 'caption', 'title', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['caption', 'title']
    ordering = ['sl_number']
    fieldsets = (
        ('Basic Information', {
            'fields': ('sl_number', 'caption', 'title', 'is_active')
        }),
        ('Main Image', {
            'fields': ('picture', 'cropping')
        }),
        ('Content', {
            'fields': ('description',)
        }),
    )


@admin.register(HeroTags)
class HeroTagsAdmin(admin.ModelAdmin):
    list_display = ['sl', 'title', 'is_active', '__str__']
    list_editable = ['title', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title']
    ordering = ['sl']
    fields = ['sl', 'title', 'is_active']


@admin.register(AdmissionElement)
class AdmissionElementAdmin(admin.ModelAdmin):
    list_display = ['sl', 'title', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'content']
    ordering = ['sl']
    fieldsets = (
        ('Basic Information', {
            'fields': ('sl', 'title')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Curriculum PDF', {
            'fields': ('curriculum_pdf',),
            'description': 'Upload curriculum PDF for BSc and MCSE programs'
        }),
    )


@admin.register(AcademicCalendar)
class AcademicCalendarAdmin(admin.ModelAdmin):
    list_display = ['year', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['year']
    ordering = ['-created_at']
    fieldsets = (
        ('Calendar Information', {
            'fields': ('year', 'pdf')
        }),
    )


@admin.register(Curricula)
class CurriculaAdmin(admin.ModelAdmin):
    list_display = ['short_title', 'program', 'publishing_year', 'version', 'running_since_year', 'running_since_semester', 'created_at']
    list_filter = ['program', 'publishing_year', 'running_since_year', 'running_since_semester', 'created_at', 'updated_at']
    search_fields = ['short_title', 'running_since_year']
    ordering = ['program', '-running_since_year', 'running_since_semester', '-version']
    fieldsets = (
        ('Curriculum Information', {
            'fields': ('short_title', 'program', 'publishing_year', 'version', 'pdf')
        }),
        ('Running Since', {
            'fields': ('running_since_year', 'running_since_semester'),
            'description': 'When this curriculum started running. Spring comes before Fall in sorting.'
        }),
    )
