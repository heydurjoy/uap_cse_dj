# How to Browse Media Files in Railway

## Method 1: Using Railway Web Interface (Easiest) ✅

### Step-by-Step:

1. **Go to Railway Dashboard**
   - Visit: https://railway.app
   - Login to your account
   - Select your project

2. **Open Your Django Service**
   - Click on your `uap_cse_dj` service (or whatever your service is named)

3. **Open the Terminal/Connect Tab**
   - Click on **"Connect"** or **"Terminal"** tab
   - This opens a web-based terminal connected to your Railway container

4. **Navigate to Media Directory**
   ```bash
   cd /app/media
   ls -la
   ```

5. **Browse Subdirectories**
   ```bash
   # List all folders
   ls -la
   
   # Browse specific folder
   cd feature_cards
   ls -la
   
   # Go back
   cd ..
   
   # Browse another folder
   cd faculty_photos
   ls -la
   ```

6. **View File Details**
   ```bash
   # See file sizes and details
   ls -lh
   
   # Count files in a directory
   find . -type f | wc -l
   
   # See total size of directory
   du -sh .
   ```

## Method 2: Using Railway CLI (More Powerful)

### Install Railway CLI:
```bash
npm install -g @railway/cli
```

### Login and Connect:
```bash
# Login to Railway
railway login

# Link to your project
railway link

# Select your service
railway service
```

### Browse Files:
```bash
# Open a shell in your Railway container
railway run bash

# Navigate to media directory
cd /app/media

# List files
ls -la

# Browse folders
cd feature_cards
ls -la

# Exit when done
exit
```

### Download Files (if needed):
```bash
# Railway CLI doesn't have direct file download, but you can:
# 1. Use the web interface terminal to view files
# 2. Access files via your website URL: https://your-site.com/media/path/to/file.jpg
```

## Method 3: Access Files via Web Browser

### Direct URL Access:

Your media files are served at:
```
https://your-railway-app.up.railway.app/media/[file-path]
```

**Examples:**
- Feature card: `https://your-app.up.railway.app/media/feature_cards/image.jpg`
- Faculty photo: `https://your-app.up.railway.app/media/faculty_photos/photo.jpg`
- Club logo: `https://your-app.up.railway.app/media/club_assets/logos/logo.png`

### Find File Paths:

1. **Via Django Admin:**
   - Go to your admin panel
   - Navigate to any model with images (FeatureCard, Faculty, etc.)
   - Click on an object
   - The file field will show the path (e.g., `feature_cards/image.jpg`)
   - Construct the full URL: `https://your-app.up.railway.app/media/feature_cards/image.jpg`

2. **Via Database (if you have access):**
   - Check the file field in your database
   - The path is stored relative to `MEDIA_ROOT`

## Method 4: List All Media Files via Django Shell

### Access Django Shell:
```bash
# Via Railway CLI
railway run python manage.py shell

# Or via Railway web terminal
cd /app
python manage.py shell
```

### List Files in Python:
```python
import os
from django.conf import settings

# List all files in media directory
media_root = settings.MEDIA_ROOT
print(f"Media root: {media_root}")

# List all files recursively
for root, dirs, files in os.walk(media_root):
    for file in files:
        file_path = os.path.join(root, file)
        relative_path = os.path.relpath(file_path, media_root)
        file_size = os.path.getsize(file_path)
        print(f"{relative_path} - {file_size} bytes")
```

## Method 5: Create a Django Admin View (Advanced)

You could create a custom Django admin view to browse files, but the methods above are simpler.

## Quick Commands Reference

### In Railway Terminal:

```bash
# Navigate to media
cd /app/media

# List all directories
ls -d */

# List all files recursively
find . -type f

# Count files
find . -type f | wc -l

# Find large files (>1MB)
find . -type f -size +1M

# Get total size
du -sh .

# List files with sizes
ls -lh

# Search for specific file
find . -name "*.jpg"

# View file contents (for text files)
cat path/to/file.txt

# Check disk usage
df -h
```

## Common Media Directories

Based on your Django models, your media files are organized as:

- `/app/media/feature_cards/` - Feature card images
- `/app/media/faculty_photos/` - Faculty profile pictures
- `/app/media/user_profiles/` - BaseUser profile pictures
- `/app/media/club_assets/logos/` - Club logos
- `/app/media/club_assets/covers/` - Club cover photos
- `/app/media/posts/attachments/` - Post attachments (PDFs)
- `/app/media/class_routines/` - Class routine images
- And more...

## Tips

1. **Use Railway Web Terminal** - It's the easiest way to browse files
2. **Bookmark Direct URLs** - If you frequently access specific files
3. **Check File Sizes** - Use `du -sh` to see directory sizes
4. **Monitor Storage** - Keep an eye on volume size limits
5. **Backup Important Files** - Download critical files periodically

## Troubleshooting

### Can't See Files?
- Check if volume is mounted: `ls -la /app/media`
- Verify mount path is `/app/media` (not `/media`)
- Check file permissions: `ls -la /app/media/`

### Files Not Showing in Browser?
- Check Django `MEDIA_URL` setting
- Verify `urls.py` serves media files
- Check Railway logs for errors

### Permission Denied?
- Files should be readable by the Django process
- Check volume permissions in Railway dashboard

## Summary

**Easiest Method:** Railway Web Interface → Connect Tab → Terminal → `cd /app/media` → `ls -la`

**Quick Access:** Use direct URLs: `https://your-app.up.railway.app/media/[path]`

**Power User:** Railway CLI → `railway run bash` → Navigate and explore

