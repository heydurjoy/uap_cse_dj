from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from people.models import BaseUser, ClubMember, AllowedEmail


class Command(BaseCommand):
    help = 'Create 10 club member users (clubm1 to clubm10)'

    def handle(self, *args, **options):
        password = 'fffjjj21'
        hashed_password = make_password(password)
        
        created_count = 0
        skipped_count = 0
        
        for i in range(1, 11):
            username = f'clubm{i}'
            email = f'clubm{i}@g.com'
            
            # Check if user already exists
            if BaseUser.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'User {username} already exists. Skipping...'))
                skipped_count += 1
                continue
            
            if BaseUser.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f'Email {email} already exists. Skipping...'))
                skipped_count += 1
                continue
            
            try:
                # Create or get AllowedEmail
                allowed_email, _ = AllowedEmail.objects.get_or_create(
                    email=email,
                    defaults={
                        'user_type': 'club_member',
                        'access_level': '1',  # Level 1 is Club Member (lowest access)
                        'is_active': True,
                        'is_blocked': False,
                    }
                )
                
                # Create BaseUser
                base_user = BaseUser.objects.create(
                    username=username,
                    email=email,
                    password=hashed_password,
                    user_type='club_member',
                    access_level='1',  # Level 1 is Club Member (lowest access)
                    allowed_email=allowed_email,
                    is_active=True,
                    is_staff=False,
                    is_superuser=False,
                )
                
                # Create ClubMember profile
                club_member = ClubMember.objects.create(
                    base_user=base_user,
                    name=f'Club Member {i}',
                    student_id=f'CM{i:03d}',  # CM001, CM002, etc.
                )
                
                self.stdout.write(self.style.SUCCESS(f'Successfully created: {username} ({email})'))
                created_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating {username}: {str(e)}'))
                skipped_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nCompleted! Created: {created_count}, Skipped: {skipped_count}'))

