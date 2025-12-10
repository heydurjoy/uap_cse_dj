from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import models
from people.models import Officer

BaseUser = get_user_model()


class Command(BaseCommand):
    help = 'Create officers in the database'

    def handle(self, *args, **options):
        password = 'fffjjj21'
        
        officers_data = [
            {'name': 'suza bhai', 'username': 'suza_bhai', 'email': 'suza@example.com'},
            {'name': 'kabir bhai', 'username': 'kabir_bhai', 'email': 'kabir@example.com'},
        ]
        
        # Get the maximum sl value to assign new serial numbers
        max_sl = Officer.objects.aggregate(max_sl=models.Max('sl'))['max_sl'] or 0
        
        for idx, officer_data in enumerate(officers_data, start=1):
            name = officer_data['name']
            username = officer_data['username']
            email = officer_data['email']
            
            # Check if user already exists
            if BaseUser.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'User {username} already exists. Skipping...')
                )
                continue
            
            # Check if officer already exists
            if Officer.objects.filter(name=name).exists():
                self.stdout.write(
                    self.style.WARNING(f'Officer {name} already exists. Skipping...')
                )
                continue
            
            try:
                # Create BaseUser
                user = BaseUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    user_type='officer',
                    access_level='2',  # General User access level
                    first_name=name.split()[0] if name.split() else '',
                )
                
                # Create Officer
                officer = Officer.objects.create(
                    base_user=user,
                    name=name,
                    sl=max_sl + idx,
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created officer: {name} (sl: {officer.sl})')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating officer {name}: {str(e)}')
                )

