# Generated manually to update publication rankings from A1-A4 to A*, A, B, C

from django.db import migrations


def update_rankings(apps, schema_editor):
    """Update existing publication rankings from a1-a4 to a_star, a, b, c"""
    Publication = apps.get_model('people', 'Publication')
    
    # Mapping: old value -> new value
    mapping = {
        'a1': 'a_star',
        'a2': 'a',
        'a3': 'b',
        'a4': 'c',
    }
    
    # Update each publication
    for old_rank, new_rank in mapping.items():
        Publication.objects.filter(ranking=old_rank).update(ranking=new_rank)


def reverse_update_rankings(apps, schema_editor):
    """Reverse migration: convert back from a_star, a, b, c to a1, a2, a3, a4"""
    Publication = apps.get_model('people', 'Publication')
    
    # Reverse mapping: new value -> old value
    reverse_mapping = {
        'a_star': 'a1',
        'a': 'a2',
        'b': 'a3',
        'c': 'a4',
    }
    
    # Update each publication
    for new_rank, old_rank in reverse_mapping.items():
        Publication.objects.filter(ranking=new_rank).update(ranking=old_rank)


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0033_add_club_to_allowedemail'),
    ]

    operations = [
        migrations.RunPython(update_rankings, reverse_update_rankings),
    ]

