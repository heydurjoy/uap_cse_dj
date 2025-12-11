# Generated manually to update ClubPost fields

import ckeditor.fields
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def migrate_publish_date_to_created_at(apps, schema_editor):
    """Copy publish_date to created_at for existing records"""
    ClubPost = apps.get_model('clubs', 'ClubPost')
    for post in ClubPost.objects.all():
        if post.publish_date:
            post.created_at = post.publish_date
            post.save()


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0005_alter_clubposition_options_clubposition_sl'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add new fields first
        migrations.AddField(
            model_name='clubpost',
            name='post_type',
            field=models.CharField(choices=[('event', 'Event'), ('seminar', 'Seminar'), ('contest', 'Contest'), ('workshop', 'Workshop'), ('training', 'Training'), ('other', 'Other')], default='event', help_text='Category of the post: Event, Seminar, Contest, Workshop, Training, or Other', max_length=20),
        ),
        migrations.AddField(
            model_name='clubpost',
            name='short_title',
            field=models.CharField(help_text='Short, display title (max 50 characters)', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='clubpost',
            name='long_title',
            field=models.CharField(help_text='Detailed headline for the announcement', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='clubpost',
            name='tags',
            field=models.CharField(blank=True, help_text="Comma-separated tags (e.g., 'signup, deadline')", max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='clubpost',
            name='description',
            field=ckeditor.fields.RichTextField(help_text='Main body content with rich text formatting', null=True),
        ),
        migrations.AddField(
            model_name='clubpost',
            name='start_date_time',
            field=models.DateTimeField(blank=True, help_text='Optional start date/time for events/workshops', null=True),
        ),
        migrations.AddField(
            model_name='clubpost',
            name='end_date_time',
            field=models.DateTimeField(blank=True, help_text='Optional end date/time for event duration', null=True),
        ),
        migrations.AddField(
            model_name='clubpost',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, help_text='Records creation time'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='clubpost',
            name='last_edited_by',
            field=models.ForeignKey(blank=True, help_text='The last user who saved/edited this post', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='last_edited_club_posts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='clubpost',
            name='last_edited_at',
            field=models.DateTimeField(auto_now=True, help_text='Records last modification time'),
        ),
        
        # Migrate data from old fields to new fields
        migrations.RunPython(migrate_publish_date_to_created_at, migrations.RunPython.noop),
        
        # Copy title to short_title and long_title
        migrations.RunPython(
            lambda apps, schema_editor: [
                post.__class__.objects.filter(pk=post.pk).update(
                    short_title=post.title[:50] if post.title else '',
                    long_title=post.title if post.title else ''
                ) for post in apps.get_model('clubs', 'ClubPost').objects.all()
            ],
            migrations.RunPython.noop
        ),
        
        # Copy content to description
        migrations.RunPython(
            lambda apps, schema_editor: [
                post.__class__.objects.filter(pk=post.pk).update(description=post.content)
                for post in apps.get_model('clubs', 'ClubPost').objects.all()
            ],
            migrations.RunPython.noop
        ),
        
        # Copy created_by to posted_by
        migrations.RunPython(
            lambda apps, schema_editor: [
                post.__class__.objects.filter(pk=post.pk).update(posted_by=post.created_by)
                for post in apps.get_model('clubs', 'ClubPost').objects.all()
            ],
            migrations.RunPython.noop
        ),
        
        # Make new required fields non-nullable
        migrations.AlterField(
            model_name='clubpost',
            name='short_title',
            field=models.CharField(help_text='Short, display title (max 50 characters)', max_length=50),
        ),
        migrations.AlterField(
            model_name='clubpost',
            name='long_title',
            field=models.CharField(help_text='Detailed headline for the announcement', max_length=255),
        ),
        migrations.AlterField(
            model_name='clubpost',
            name='description',
            field=ckeditor.fields.RichTextField(help_text='Main body content with rich text formatting'),
        ),
        migrations.AlterField(
            model_name='clubpost',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, help_text='Records creation time'),
        ),
        
        # Rename created_by to posted_by (if needed, or just remove old field)
        migrations.RenameField(
            model_name='clubpost',
            old_name='created_by',
            new_name='posted_by',
        ),
        
        # Remove old fields
        migrations.RemoveField(
            model_name='clubpost',
            name='title',
        ),
        migrations.RemoveField(
            model_name='clubpost',
            name='content',
        ),
        migrations.RemoveField(
            model_name='clubpost',
            name='publish_date',
        ),
        migrations.RemoveField(
            model_name='clubpost',
            name='updated_at',
        ),
        
        # Update Meta ordering
        migrations.AlterModelOptions(
            name='clubpost',
            options={'ordering': ['-is_pinned', '-created_at'], 'verbose_name': 'Club Post', 'verbose_name_plural': 'Club Posts'},
        ),
    ]
