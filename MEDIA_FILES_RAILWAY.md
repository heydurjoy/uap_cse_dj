# Media Files on Railway - Important Information

## The Problem

When you deploy to Railway, **media files uploaded locally are not automatically transferred**. Railway's filesystem is **ephemeral**, meaning:

1. Files uploaded locally stay on your computer
2. When you deploy, Railway starts with an empty `media/` directory
3. The database has the correct file paths, but the actual files don't exist on Railway
4. This causes "Not Found" errors for all media files

## Current Solution

I've updated the code to **serve media files in production** (previously they were only served in development). However, this only solves the serving issue - **you still need to get the files onto Railway**.

## Options to Fix This

### Option 1: Upload Media Files to Railway (Quick Fix)

After deploying, you can upload media files manually:

1. **Using Railway CLI:**
   ```bash
   railway run bash
   # Then copy files or use scp/sftp
   ```

2. **Using Railway Volumes (Recommended for persistent storage):**
   - Go to your Railway project
   - Add a Volume service
   - Mount it to `/media` in your Django service
   - Upload your local `media/` folder to the volume

3. **Re-upload through Django Admin:**
   - Access your Railway app's admin panel
   - Re-upload all images through the admin interface

### Option 2: Use Cloud Storage (Best Practice)

For production, use cloud storage services:

#### AWS S3 (Recommended)
1. Install `django-storages` and `boto3`:
   ```bash
   pip install django-storages boto3
   ```

2. Update `settings.py`:
   ```python
   INSTALLED_APPS = [
       # ... existing apps ...
       'storages',
   ]
   
   # AWS S3 Settings
   AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
   AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
   AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
   AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
   AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
   
   # Use S3 for media files
   DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
   MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
   ```

3. Set environment variables in Railway:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_STORAGE_BUCKET_NAME`
   - `AWS_S3_REGION_NAME`

#### Cloudinary (Alternative)
1. Install `django-cloudinary-storage`:
   ```bash
   pip install django-cloudinary-storage
   ```

2. Update `settings.py`:
   ```python
   INSTALLED_APPS = [
       # ... existing apps ...
       'cloudinary_storage',
       'django.contrib.staticfiles',
       'cloudinary',
   ]
   
   CLOUDINARY_STORAGE = {
       'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
       'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
       'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
   }
   
   DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
   ```

### Option 3: Commit Media Files to Git (Not Recommended)

⚠️ **Warning**: This is not recommended for production as it:
- Increases repository size
- Makes deployments slower
- Can cause issues with large files

If you must do this temporarily:
1. Remove `media/` from `.gitignore`
2. Commit media files
3. Push to repository
4. Railway will include them in deployment

## Immediate Steps

1. **The code is now fixed** - media files will be served in production
2. **You need to upload your media files** to Railway using one of the options above
3. **For future uploads**, use cloud storage or Railway Volumes

## Testing

After uploading media files, check:
- `/media/feature_cards/` - Should show feature card images
- `/media/faculty_photos/` - Should show faculty photos
- `/static/defaults/people.png` - Should show default profile picture

## Notes

- Static files (CSS, JS) are handled by WhiteNoise and should work automatically
- The `collectstatic` command in `railway.toml` collects static files during build
- Media files require manual handling or cloud storage








