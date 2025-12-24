# Volume Setup - Complete Guide

## ✅ Volume is Mounted - Next Steps

### Step 1: Verify Volume is Correctly Mounted

1. Go to your Railway `uap_cse_dj` service
2. Check the **"Volumes"** section
3. Confirm the volume is mounted at: `/app/media`
4. The volume should show as "Attached" or "Mounted"

### Step 2: Upload Your Existing Media Files

You have 3 options:

#### Option A: Re-upload via Django Admin (Easiest - Recommended)

1. **Access your Railway app's admin panel:**
   - Go to: `https://uapcsedj-production.up.railway.app/admin/`
   - Login with your admin credentials

2. **Re-upload images for each model:**
   - **Feature Cards**: Go to Designs → Feature Cards → Edit each card → Re-upload image
   - **Faculty Photos**: Go to People → Faculties → Edit each faculty → Re-upload profile pic
   - **Club Assets**: Go to Clubs → Clubs → Edit each club → Re-upload logo and cover photo
   - **Officer Photos**: Go to People → Officers → Edit each officer → Re-upload photo
   - **Any other models with images**

3. **Files will automatically save to the volume** at `/app/media/`

#### Option B: Using Railway CLI

1. **Install Railway CLI** (if not already installed):
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and link:**
   ```bash
   railway login
   railway link
   ```

3. **Copy files from local to Railway:**
   ```bash
   # From your local project directory
   railway run bash
   
   # Inside the container, you can use scp or other methods
   # Or use Railway's file transfer features
   ```

#### Option C: Using Railway Web Interface

1. Go to your service → **"Connect"** tab
2. Use the file browser/terminal
3. Upload files to `/app/media/` directory

### Step 3: Verify Files are in Volume

1. **Check via Railway Dashboard:**
   - Go to your service → Connect tab
   - Navigate to `/app/media/`
   - You should see your folders: `feature_cards/`, `faculty_photos/`, etc.

2. **Check via Django Admin:**
   - Upload a test image
   - Check if it appears on your website
   - If it does, the volume is working!

### Step 4: Test After Deployment

1. **Make a small code change and push:**
   ```bash
   git commit --allow-empty -m "Test volume persistence"
   git push
   ```

2. **After deployment completes:**
   - Check your website
   - Images should still be there! ✅

## ✅ How It Works Now

### What Happens on Each Push:

1. **Code gets deployed** → New container is created
2. **Volume stays mounted** → Your `/app/media/` folder persists
3. **Files remain** → All images stay in the volume
4. **No data loss** → Images won't disappear! 🎉

### Future Uploads:

- **New images uploaded** → Automatically save to `/app/media/` (the volume)
- **Files persist** → They'll survive all future deployments
- **No action needed** → Django handles everything automatically

## 🔍 Troubleshooting

### Images Still Not Showing?

1. **Check volume mount path:**
   - Must be exactly `/app/media`
   - Not `/media` or any other path

2. **Check Django settings:**
   - Make sure `CLOUDINARY_*` variables are NOT set
   - Django should use local filesystem (the volume)

3. **Check file permissions:**
   - Volume should have read/write permissions
   - Django service should have access

4. **Check Railway logs:**
   - Look for any errors related to file access
   - Check if volume is properly attached

### Verify Volume is Working:

```bash
# In Railway service terminal
ls -la /app/media/
# Should show your folders and files
```

## 📝 Summary

✅ **Volume mounted** → Check it's at `/app/media`  
✅ **Upload existing files** → Use Django admin (easiest)  
✅ **Test deployment** → Push code, images should persist  
✅ **Future uploads** → Automatically go to volume  

**You're all set!** Images will now persist across all deployments! 🚀

