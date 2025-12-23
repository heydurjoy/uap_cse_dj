# Generated manually to add missing description field

import ckeditor.fields
from django.db import migrations, connection


def add_description_if_not_exists(apps, schema_editor):
    """Add description field only if it doesn't already exist"""
    with connection.cursor() as cursor:
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='clubs_clubpost' AND column_name='description'
        """)
        exists = cursor.fetchone()
        
        if not exists:
            # Column doesn't exist, add it
            cursor.execute("""
                ALTER TABLE clubs_clubpost 
                ADD COLUMN description TEXT NOT NULL DEFAULT ''
            """)
            # Update default to empty string for existing rows
            cursor.execute("""
                UPDATE clubs_clubpost 
                SET description = '' 
                WHERE description IS NULL
            """)


def remove_description_if_exists(apps, schema_editor):
    """Remove description field if it exists"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='clubs_clubpost' AND column_name='description'
        """)
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute("ALTER TABLE clubs_clubpost DROP COLUMN description")


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0007_alter_clubpost_is_pinned_alter_clubpost_posted_by'),
    ]

    operations = [
        migrations.RunPython(
            add_description_if_not_exists,
            reverse_code=remove_description_if_exists,
        ),
    ]
