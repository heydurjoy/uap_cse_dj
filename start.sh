#!/bin/bash
# Railway startup script - runs migrations and starts the server

set -e  # Exit on any error

echo "🚀 Starting Railway deployment..."

# Run all migrations (this will run migrations for all apps including people and clubs)
echo "📦 Running database migrations..."
python manage.py migrate --noinput

# Collect static files (if not done in build)
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️ Static files collection completed with warnings"

# Start Gunicorn
echo "✅ Starting Gunicorn server..."
exec gunicorn uap_cse_dj.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120

