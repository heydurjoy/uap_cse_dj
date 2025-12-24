# Cloudinary Setup for Media Files

## Why Cloudinary?

- ✅ **Files persist across deployments** - No more lost images!
- ✅ **Free tier available** - 25GB storage, 25GB bandwidth/month
- ✅ **Automatic image optimization** - Faster loading
- ✅ **CDN included** - Global content delivery
- ✅ **No code changes needed** - Just set environment variables

## Setup Steps

### Step 1: Create Cloudinary Account

1. Go to https://cloudinary.com/users/register/free
2. Sign up for a free account
3. Verify your email

### Step 2: Get Your Credentials

1. After logging in, go to your **Dashboard**
2. You'll see your credentials:
   - **Cloud Name** (e.g., `your-cloud-name`)
   - **API Key** (e.g., `123456789012345`)
   - **API Secret** (e.g., `abcdefghijklmnopqrstuvwxyz123456`)

### Step 3: Add Environment Variables to Railway

1. Go to your Railway project dashboard
2. Select your Django service
3. Go to **"Variables"** tab
4. Add these three environment variables:

   ```
   CLOUDINARY_CLOUD_NAME = your-cloud-name
   CLOUDINARY_API_KEY = 123456789012345
   CLOUDINARY_API_SECRET = abcdefghijklmnopqrstuvwxyz123456
   ```

5. Click **"Deploy"** or Railway will auto-deploy

### Step 4: Deploy Your Code

The code is already updated! Just commit and push:

```bash
git add requirements.txt uap_cse_dj/settings.py
git commit -m "Add Cloudinary for media file storage"
git push
```

### Step 5: Upload Existing Media Files

After deployment, you need to upload your existing media files to Cloudinary:

**Option A: Using Django Admin (Easiest)**
1. Access your Railway app's admin panel
2. Go to each model that has images:
   - Feature Cards
   - Faculty photos
   - Club logos/covers
   - Officer photos
   - etc.
3. Edit each item and re-upload the image
4. Files will automatically go to Cloudinary

**Option B: Using Cloudinary Dashboard**
1. Go to Cloudinary Dashboard → Media Library
2. Upload your media files manually
3. Organize them in folders matching your Django structure:
   - `feature_cards/`
   - `faculty_photos/`
   - `club_assets/logos/`
   - `club_assets/covers/`
   - etc.

**Option C: Using Cloudinary API (Advanced)**
You can write a script to bulk upload files from your local `media/` folder.

### Step 6: Verify

1. Upload a test image through Django admin
2. Check Cloudinary Dashboard → Media Library - you should see it
3. Check your website - image should load from Cloudinary CDN

## How It Works

- **Local Development**: Uses local filesystem (no Cloudinary needed)
- **Production (Railway)**: Uses Cloudinary if credentials are set
- **Automatic**: Django automatically chooses based on environment variables

## Benefits

- 🚀 **No more lost files** - Images persist across deployments
- ⚡ **Faster loading** - CDN delivers images globally
- 🖼️ **Image optimization** - Automatic compression and formats
- 💰 **Free tier** - 25GB storage, 25GB bandwidth/month
- 📈 **Scalable** - Handles traffic spikes automatically

## Troubleshooting

**Images not showing?**
- Check that all three environment variables are set in Railway
- Verify credentials in Cloudinary Dashboard
- Check Railway logs for errors

**Want to switch back to local storage?**
- Remove the three `CLOUDINARY_*` environment variables from Railway
- Redeploy

## Free Tier Limits

- **Storage**: 25GB
- **Bandwidth**: 25GB/month
- **Transformations**: 25,000/month
- **Uploads**: 5,000/month

For most small-to-medium sites, this is plenty! Upgrade if needed.

