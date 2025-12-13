"""
Management command to sync is_power_user from AllowedEmail to BaseUser.
This ensures that if an AllowedEmail is marked as a power user,
the corresponding BaseUser is also updated.
"""
from django.core.management.base import BaseCommand
from people.models import BaseUser, AllowedEmail


class Command(BaseCommand):
    help = 'Sync is_power_user from AllowedEmail to BaseUser'

    def handle(self, *args, **options):
        synced_count = 0
        updated_count = 0
        
        # Sync from AllowedEmail to BaseUser
        for allowed_email in AllowedEmail.objects.filter(is_power_user=True):
            try:
                user = allowed_email.base_user
                if user and not user.is_power_user:
                    user.is_power_user = True
                    user.save()
                    synced_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Synced: {user.email} (now a power user)')
                    )
            except BaseUser.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'○ No BaseUser found for AllowedEmail: {allowed_email.email}')
                )
        
        # Also check for BaseUsers that should be power users but aren't
        for user in BaseUser.objects.filter(is_power_user=False):
            if user.allowed_email and user.allowed_email.is_power_user:
                user.is_power_user = True
                user.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Updated: {user.email} (now a power user)')
                )
        
        total = synced_count + updated_count
        if total > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Completed! Synced/Updated {total} user(s) to power users.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✓ All power users are already synced.')
            )

