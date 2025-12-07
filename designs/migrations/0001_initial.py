# Generated manually
from django.db import migrations, models
import ckeditor.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FeatureCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sl_number', models.IntegerField(help_text='Serial number for ordering', unique=True)),
                ('picture', models.ImageField(help_text='Main picture for the card', upload_to='feature_cards/')),
                ('caption', models.CharField(help_text='Short caption displayed on the card', max_length=200)),
                ('title', models.CharField(help_text='Title for the detail page', max_length=200)),
                ('description', ckeditor.fields.RichTextField(help_text='Detailed description with rich text formatting')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True, help_text='Show/hide this card')),
            ],
            options={
                'verbose_name': 'Feature Card',
                'verbose_name_plural': 'Feature Cards',
                'ordering': ['sl_number'],
            },
        ),
        migrations.CreateModel(
            name='FeatureCardImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(help_text='Additional picture for detail view', upload_to='feature_cards/detail/')),
                ('caption', models.CharField(blank=True, help_text='Optional caption for this image', max_length=200)),
                ('order', models.IntegerField(default=0, help_text='Order of display')),
                ('feature_card', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detail_images', to='designs.featurecard')),
            ],
            options={
                'verbose_name': 'Feature Card Detail Image',
                'verbose_name_plural': 'Feature Card Detail Images',
                'ordering': ['order', 'id'],
            },
        ),
    ]

