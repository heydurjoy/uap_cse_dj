"""
Django management command to import production data.
Can be run via Railway CLI or added to deployment.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
import os


class Command(BaseCommand):
    help = 'Import production data from production_data.json'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='production_data.json',
            help='Path to the JSON file to import',
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return
        
        self.stdout.write(f'Starting import from {file_path}...')
        
        try:
            call_command(
                'loaddata',
                file_path,
                ignorenonexistent=True,
                verbosity=2,  # Show progress
            )
            self.stdout.write(
                self.style.SUCCESS('✅ Import completed successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during import: {e}')
            )
            raise

