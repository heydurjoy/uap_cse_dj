@echo off
REM Railway startup script for Windows (local testing)
REM Note: Railway uses Linux, so start.sh is the actual script used

echo Starting Railway deployment...

REM Run all migrations
echo Running database migrations...
python manage.py migrate --noinput

REM Run migrations for specific apps
echo Running migrations for people app...
python manage.py migrate people --noinput

echo Running migrations for clubs app...
python manage.py migrate clubs --noinput

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

REM Start Gunicorn (for local testing, Railway uses the startCommand in railway.toml)
echo Starting Gunicorn server...
gunicorn uap_cse_dj.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120

