#!/usr/bin/env python
"""
Simple script to export all data from Django database to JSON file.
Works with both SQLite and PostgreSQL.

Usage:
    python export_data.py [output_file.json]
    
If no output file is specified, defaults to 'data_export.json'
"""

import os
import sys
import django
from pathlib import Path
import io

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uap_cse_dj.settings')
django.setup()

from django.core.management import call_command
from django.core import serializers
from django.apps import apps

def export_data(output_file='data_export.json'):
    """
    Export all data from the database to a JSON file.
    
    Excludes:
    - auth.permission (auto-generated)
    - contenttypes (auto-generated)
    """
    print(f"Starting data export...")
    print(f"Output file: {output_file}")
    
    try:
        # Get all models except excluded ones
        excluded_apps = ['auth.permission', 'contenttypes']
        all_models = []
        
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                model_name = f"{app_config.label}.{model.__name__}"
                if model_name not in excluded_apps:
                    all_models.append(model)
        
        # Serialize all data
        print("Serializing data...")
        data = serializers.serialize(
            "json",
            [obj for model in all_models for obj in model.objects.all()],
            indent=2,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
        )
        
        # Write to file with explicit UTF-8 encoding
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(data)
        
        file_size = os.path.getsize(output_file)
        print(f"\n✅ Export completed successfully!")
        print(f"📁 File: {output_file}")
        print(f"📊 Size: {file_size / 1024:.2f} KB")
        print(f"\nTo import this data, run:")
        print(f"  python manage.py loaddata {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error during export: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    # Get output filename from command line or use default
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'data_export.json'
    export_data(output_file)

