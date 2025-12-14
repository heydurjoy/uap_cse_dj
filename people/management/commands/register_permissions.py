"""
Management command to register permissions from permissions.py.
This can be run anytime to ensure all permissions are registered.
Useful for adding new permissions without creating migrations.
"""

from django.core.management.base import BaseCommand
from people.models import Permission
from people.permissions import PERMISSION_DEFINITIONS


class Command(BaseCommand):
    help = 'Register all permissions from permissions.py definitions'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for perm_def in PERMISSION_DEFINITIONS:
            permission, created = Permission.objects.get_or_create(
                codename=perm_def['codename'],
                defaults={
                    'name': perm_def['name'],
                    'description': perm_def.get('description', ''),
                    'category': perm_def.get('category', ''),
                    'requires_role': perm_def.get('requires_role', []),
                    'priority': perm_def.get('priority', 100),
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created permission: {permission.name} ({permission.codename})')
                )
            else:
                # Update existing permission if needed
                updated = False
                if permission.name != perm_def['name']:
                    permission.name = perm_def['name']
                    updated = True
                if permission.description != perm_def.get('description', ''):
                    permission.description = perm_def.get('description', '')
                    updated = True
                if permission.category != perm_def.get('category', ''):
                    permission.category = perm_def.get('category', '')
                    updated = True
                if permission.requires_role != perm_def.get('requires_role', []):
                    permission.requires_role = perm_def.get('requires_role', [])
                    updated = True
                if permission.priority != perm_def.get('priority', 100):
                    permission.priority = perm_def.get('priority', 100)
                    updated = True
                if not permission.is_active:
                    permission.is_active = True
                    updated = True
                
                if updated:
                    permission.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ Updated permission: {permission.name} ({permission.codename})')
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'○ Skipped (already exists): {permission.name} ({permission.codename})')
                    )
        
        self.stdout.write(self.style.SUCCESS(
            f'\nCompleted! Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}'
        ))


