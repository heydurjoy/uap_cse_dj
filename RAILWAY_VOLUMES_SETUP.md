# Railway Volumes Setup for Media Files

## Quick Setup Guide

### Step 1: Create a Volume in Railway

1. Go to your Railway project dashboard
2. Click **"+ New"** → **"Volume"**
3. Name it: `media-storage`
4. Set the mount path: `/media`
5. Click **"Deploy"**

### Step 2: Link Volume to Your Django Service

1. Go to your Django service settings
2. Find **"Volumes"** section
3. Add the volume you just created
4. Set mount path to: `/media`

### Step 3: Upload Your Media Files

**Option A: Using Railway CLI (Recommended)**

1. Install Railway CLI: https://docs.railway.app/develop/cli
2. Login: `railway login`
3. Link to your project: `railway link`
4. Upload files:
   ```bash
   # Navigate to your project directory
   cd /path/to/your/project
   
   # Copy media files to Railway volume
   railway run --service your-service-name bash
   # Then inside the container:
   # You can use scp or rsync to copy files
   ```

**Option B: Using Railway Web Interface**

1. Go to your service → **"Connect"** tab
2. Use the file browser to upload files to `/media`

**Option C: Re-upload via Django Admin**

1. Access your Railway app's admin panel
2. Go to each model (FeatureCard, Faculty, Club, etc.)
3. Re-upload images through the admin interface
4. Files will now persist in the volume

### Step 4: Verify

After uploading, check:
- `/media/feature_cards/` - Should show images
- `/media/faculty_photos/` - Should show photos
- `/media/club_assets/` - Should show club logos/covers

## Important Notes

- ✅ **Files in volumes persist across deployments**
- ✅ **No code changes needed** - Django will automatically use the volume
- ⚠️ **Volume size limits** - Check Railway pricing for volume storage limits
- ⚠️ **Backup recommended** - Consider backing up important media files

## Alternative: Cloud Storage

If you prefer cloud storage (S3, Cloudinary), see `MEDIA_FILES_RAILWAY.md` for setup instructions.

