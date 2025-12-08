# Generated migration for adding initial HeroTags

from django.db import migrations

def create_initial_hero_tags(apps, schema_editor):
    HeroTags = apps.get_model('designs', 'HeroTags')
    
    hero_tags_data = [
        {'sl': 1, 'title': '1400+ Students'},
        {'sl': 2, 'title': '20k+ Graduates'},
        {'sl': 3, 'title': 'Largest Dept. of UAP'},
        {'sl': 4, 'title': '50+ Faculty'},
        {'sl': 5, 'title': '9 Clubs & Societies'},
        {'sl': 6, 'title': 'JRC Scholarship'},
    ]
    
    for tag_data in hero_tags_data:
        HeroTags.objects.get_or_create(
            sl=tag_data['sl'],
            defaults={'title': tag_data['title']}
        )

def remove_initial_hero_tags(apps, schema_editor):
    HeroTags = apps.get_model('designs', 'HeroTags')
    HeroTags.objects.filter(sl__in=[1, 2, 3, 4, 5, 6]).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('designs', '0004_herotags'),
    ]

    operations = [
        migrations.RunPython(create_initial_hero_tags, remove_initial_hero_tags),
    ]

