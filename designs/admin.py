from django.contrib import admin
from image_cropping import ImageCroppingMixin
from .models import FeatureCard, HeroTags

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

