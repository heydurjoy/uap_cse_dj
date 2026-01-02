# Generated manually
from django.db import migrations, models
import ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0034_update_publication_rankings'),
    ]

    operations = [
        migrations.AddField(
            model_name='faculty',
            name='is_phd',
            field=models.BooleanField(blank=True, default=False, help_text='Whether the faculty member has a PhD degree', null=True),
        ),
        migrations.AddField(
            model_name='faculty',
            name='is_masters',
            field=models.BooleanField(blank=True, default=False, help_text='Whether the faculty member has a Masters degree', null=True),
        ),
        migrations.AddField(
            model_name='faculty',
            name='educational_qualification',
            field=ckeditor.fields.RichTextField(blank=True, help_text='Educational qualifications with rich text formatting', null=True),
        ),
        migrations.AddField(
            model_name='faculty',
            name='course_conducted',
            field=ckeditor.fields.RichTextField(blank=True, help_text='Courses conducted by the faculty member with rich text formatting', null=True),
        ),
    ]

