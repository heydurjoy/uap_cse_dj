# Generated manually to add missing description field

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0007_alter_clubpost_is_pinned_alter_clubpost_posted_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='clubpost',
            name='description',
            field=ckeditor.fields.RichTextField(
                help_text='Main body content with rich text formatting',
                default=''
            ),
            preserve_default=False,
        ),
    ]
