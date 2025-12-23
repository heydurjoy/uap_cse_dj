#!/usr/bin/env python
"""
Simple script to import data from JSON file into Django database.

Usage:
    python import_data.py [input_file.json]
    
If no input file is specified, defaults to 'data_export.json'
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uap_cse_dj.settings')
django.setup()

from django.core.management import call_command

def import_data(input_file='data_export.json'):
    """
    Import data from a JSON file into the database.
    """
    if not os.path.exists(input_file):
        print(f"❌ Error: File '{input_file}' not found!")
        sys.exit(1)
    
    print(f"Starting data import...")
    print(f"Input file: {input_file}")
    
    try:
        # Import data
        call_command(
            'loaddata',
            input_file,
            ignorenonexistent=True,  # Ignore models that don't exist
        )
        
        print(f"\n✅ Import completed successfully!")
        print(f"📁 Data from '{input_file}' has been loaded into the database.")
        
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        print(f"\nTip: If you see foreign key errors, try:")
        print(f"  python manage.py loaddata {input_file} --ignorenonexistent")
        sys.exit(1)

if __name__ == '__main__':
    # Get input filename from command line or use default
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'data_export.json'
    import_data(input_file)

