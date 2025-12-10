from django.contrib import admin
from .models import Program, ProgramOutcome, Course, CourseOutcome


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(ProgramOutcome)
class ProgramOutcomeAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'program']
    list_filter = ['program']
    search_fields = ['code', 'title', 'description']
    ordering = ['program', 'code']
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'title', 'program')
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'title', 'program', 'year_semester', 'course_type', 'credit_hours', 'contact_hours']
    list_filter = ['program', 'course_type', 'year_semester']
    search_fields = ['course_code', 'title']
    ordering = ['program', 'year_semester', 'course_code']
    filter_horizontal = ['prerequisites']
    fieldsets = (
        ('Basic Information', {
            'fields': ('program', 'course_code', 'title', 'course_type', 'year_semester')
        }),
        ('Prerequisites', {
            'fields': ('prerequisites',),
            'description': 'Select courses that must be completed before taking this course.'
        }),
        ('Hours', {
            'fields': ('credit_hours', 'contact_hours')
        }),
        ('Course Outline', {
            'fields': ('course_outline_pdf',)
        }),
    )


@admin.register(CourseOutcome)
class CourseOutcomeAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'course', 'program_outcome', 'blooms_level', 'knowledge_profile']
    list_filter = ['course__program', 'course', 'blooms_level', 'knowledge_profile', 'problem_attribute']
    search_fields = ['statement', 'course__course_code', 'program_outcome__code']
    ordering = ['course', 'sequence_number']
    fieldsets = (
        ('Course Information', {
            'fields': ('course', 'sequence_number', 'statement')
        }),
        ('Program Learning Outcome Mapping', {
            'fields': ('program_outcome',)
        }),
        ('KPA Attributes', {
            'fields': ('blooms_level', 'knowledge_profile', 'problem_attribute', 'activity_attribute')
        }),
        ('Assessment & Activity', {
            'fields': ('total_assessment_marks', 'activity')
        }),
    )
