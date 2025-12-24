# Media File Cleanup - Automatic Deletion

## Overview

This document explains how media files are automatically cleaned up when:
1. **Files are replaced** (e.g., uploading a new profile picture)
2. **Objects are deleted** (e.g., deleting a Faculty member, Club, etc.)

## How It Works

### 1. File Replacement Cleanup

When you upload a new file to replace an existing one:

- **Before saving**: The `pre_save` signal detects if a file field has changed
- **Old file deletion**: If the file name is different, the old file is automatically deleted from storage
- **New file processing**: The new file is then compressed/validated as usual

**Example:**
- User has profile picture: `media/profile_pictures/user_123_old.jpg`
- User uploads new picture: `media/profile_pictures/user_123_new.jpg`
- **Result**: `user_123_old.jpg` is automatically deleted, only `user_123_new.jpg` remains

### 2. Object Deletion Cleanup

When an object with media files is deleted:

- **After deletion**: The `post_delete` signal fires
- **File cleanup**: All associated media files are automatically deleted from storage
- **Storage freed**: No orphaned files remain

**Example:**
- Faculty member with `profile_pic` and `cv` is deleted
- **Result**: Both `profile_pic` and `cv` files are automatically deleted from storage

## Models with Automatic Cleanup

The following models have automatic file cleanup:

### Image Fields
- `BaseUser.profile_picture`
- `Faculty.profile_pic`
- `Staff.profile_pic`
- `Officer.profile_pic`
- `ClubMember.profile_pic`
- `Contributor.photo`
- `Club.logo`
- `Club.cover_photo`
- `FeatureCard.picture`
- `ClassRoutine.routine_image`

### PDF/File Fields
- `Faculty.cv`
- `AdmissionElement.curriculum_pdf`
- `AcademicCalendar.pdf`
- `AdmissionResult.official_pdf`
- `PostAttachment.file`
- `Course.course_outline_pdf`

## Implementation Details

### Signal Handlers

1. **`compress_image_files` (pre_save)**
   - Detects file changes
   - Deletes old files when replaced
   - Compresses new files if needed

2. **`validate_pdf_files` (pre_save)**
   - Validates PDF file sizes
   - Prevents oversized files from being saved

3. **`delete_media_files` (post_delete)**
   - Deletes all associated files when objects are deleted
   - Prevents orphaned files from accumulating

### Safe Deletion

The `delete_file_safely()` function:
- Uses Django's storage backend when available
- Falls back to direct file system deletion if needed
- Handles errors gracefully (won't break the app if deletion fails)
- Logs warnings for debugging

## Benefits

✅ **No orphaned files**: Old files are automatically removed  
✅ **Storage efficiency**: Prevents unnecessary storage usage  
✅ **Volume management**: Keeps Railway volumes from filling up  
✅ **Automatic**: No manual cleanup required  
✅ **Safe**: Errors are handled gracefully  

## Important Notes

⚠️ **File deletion is permanent** - Deleted files cannot be recovered  
⚠️ **Deletion happens immediately** - No undo option  
⚠️ **Errors are logged** - Check logs if files aren't being deleted  

## Troubleshooting

If files aren't being deleted:

1. **Check logs**: Look for warnings about file deletion failures
2. **Check permissions**: Ensure the app has write/delete permissions on the media directory
3. **Check storage backend**: Verify Django storage backend is configured correctly
4. **Check signals**: Ensure signals are registered (check `people/apps.py`)

## Manual Cleanup (If Needed)

If you need to manually clean up orphaned files:

```python
# Django shell: python manage.py shell
from people.utils.media_processing import delete_file_safely
from people.models import Faculty

# Example: Clean up files for a specific faculty
faculty = Faculty.objects.get(pk=1)
delete_file_safely(faculty.profile_pic)
delete_file_safely(faculty.cv)
```

## Future Enhancements

Potential improvements:
- Add a management command to find and delete orphaned files
- Add file size reporting
- Add cleanup statistics/logging
- Add soft-delete option (move to trash instead of permanent deletion)

