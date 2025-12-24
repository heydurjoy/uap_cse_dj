# Reverting Code Versions on Railway - Database Impact Guide

## Quick Answer

**Yes, reverting to an old code version CAN affect your PostgreSQL database**, but it depends on how you do it. Here's what you need to know:

## Understanding the Relationship

- **Your Code** (Django app) = Lives in Git, deployed to Railway
- **Your Database** (PostgreSQL) = Separate service on Railway, persists independently
- **Migrations** = Bridge between code and database schema

## What Happens When You Revert Code?

### Scenario 1: Revert Code Only (Database Stays Current) ⚠️

If you revert your code to an old version but keep the current database:

**Potential Issues:**
1. **Schema Mismatch** - Old code expects old database structure, but database has new fields/tables
2. **Migration State Confusion** - Django thinks migrations are applied, but code doesn't match
3. **Runtime Errors** - App crashes when trying to access fields that don't exist in old code
4. **Data Loss Risk** - Old code might not handle new data structures properly

**Example:**
- Current database has a `Contributor` model (from migration 0025)
- You revert to code before Contributor was added
- Django will try to access `people_contributor` table that old code doesn't know about
- **Result:** App crashes with `django.db.utils.ProgrammingError`

### Scenario 2: Revert Code + Rollback Migrations ✅ (Safer)

If you revert code AND rollback database migrations to match:

**What Happens:**
1. Database schema matches old code
2. Migrations state is consistent
3. App should work correctly
4. **⚠️ Data Loss:** Any data in tables/fields that are removed will be lost

## Safe Reversion Process

### Step 1: Backup Your Database First! 🔴 CRITICAL

**Before doing anything, backup your data:**

```powershell
# Set your DATABASE_URL
$env:DATABASE_URL="postgresql://postgres:BDGvLvKHzWtIZJATrTwmzbgkZrvLQloV@metro.proxy.rlwy.net:25027/railway"

# Export all data
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > backup_before_revert.json
```

Or use Railway's backup feature:
1. Go to Railway dashboard → PostgreSQL service
2. Click "Backup" or "Data" tab
3. Create a backup

### Step 2: Identify Target Version

Decide which commit/version you want to revert to:
```bash
git log --oneline  # See commit history
git show <commit-hash>  # See what changed
```

### Step 3: Check Migration Differences

See what migrations exist in old vs current code:
```bash
# Check current migrations
python manage.py showmigrations

# After reverting, check again
git checkout <old-commit>
python manage.py showmigrations
```

### Step 4: Revert Code

```bash
# Option A: Revert to specific commit
git checkout <commit-hash>

# Option B: Revert to specific branch
git checkout <branch-name>

# Option C: Create new branch from old commit
git checkout -b revert-to-old-version <commit-hash>
```

### Step 5: Rollback Migrations (If Needed)

**⚠️ WARNING: This will delete data in removed tables/fields!**

```powershell
# Set DATABASE_URL
$env:DATABASE_URL="postgresql://postgres:BDGvLvKHzWtIZJATrTwmzbgkZrvLQloV@metro.proxy.rlwy.net:25027/railway"

# See what migrations need to be rolled back
python manage.py showmigrations

# Rollback specific app
python manage.py migrate people <target-migration-number>

# Rollback all to a specific migration
python manage.py migrate people 0020  # Rollback to migration 0020

# Rollback all apps (DANGEROUS!)
python manage.py migrate --fake-initial
```

### Step 6: Deploy to Railway

```bash
git push origin <branch-name>  # Push reverted code
```

Railway will automatically:
1. Build the old code
2. Run `python manage.py migrate` (which should be a no-op if you rolled back correctly)
3. Deploy the app

## What Gets Affected?

### ✅ Safe to Revert (Usually)
- **Code logic** - Views, templates, URLs
- **Static files** - CSS, JavaScript, images
- **Settings** - Configuration changes
- **New features** - Code that doesn't touch database

### ⚠️ Risky to Revert (Requires Migration Rollback)
- **Model changes** - Adding/removing fields, models
- **Database schema** - Any migration changes
- **Data relationships** - Foreign keys, many-to-many

### 🔴 Dangerous (Data Loss)
- **Removing models** - All data in that model is lost
- **Removing fields** - Data in those fields is lost
- **Changing field types** - May cause data corruption

## Example: Reverting Safely

Let's say you want to revert to before the `Contributor` model was added:

```bash
# 1. Backup first!
$env:DATABASE_URL="postgresql://postgres:BDGvLvKHzWtIZJATrTwmzbgkZrvLQloV@metro.proxy.rlwy.net:25027/railway"
python manage.py dumpdata > backup.json

# 2. Find the commit before Contributor was added
git log --oneline | grep -i contributor
# Find commit hash before 0025_contributor.py

# 3. Revert code
git checkout <commit-before-contributor>

# 4. Rollback migrations
python manage.py migrate people 0024  # Rollback to migration 0024

# 5. Verify
python manage.py showmigrations people
# Should show migrations up to 0024 applied

# 6. Test locally
python manage.py runserver
# Should work without errors

# 7. Deploy
git push origin main
```

## Alternative: Keep Database, Update Code Gradually

Instead of reverting, you can:

1. **Keep current database**
2. **Update old code** to handle new database schema
3. **Add compatibility code** to ignore new fields

Example:
```python
# In old model, add new fields as optional
class OldModel(models.Model):
    # Old fields
    name = models.CharField(max_length=100)
    
    # Add new fields as optional (won't break if they don't exist in DB)
    new_field = models.CharField(max_length=100, blank=True, null=True)
```

## Railway-Specific Considerations

### Railway's Deployment Process

When you push code to Railway:
1. Railway builds your code
2. Runs `python manage.py migrate --noinput` (from railway.toml)
3. Runs `collectstatic`
4. Starts your app

**If migrations are out of sync:**
- Railway will try to apply migrations
- If old code has migrations that database already applied → No problem
- If database has migrations that old code doesn't know about → **ERROR**

### Railway Database Backups

Railway provides automatic backups:
1. Go to PostgreSQL service → "Backups" tab
2. You can restore from a backup if something goes wrong

## Best Practices

1. **Always backup before reverting** 🔴
2. **Test locally first** - Revert locally, test, then deploy
3. **Use feature flags** - Instead of reverting, disable features
4. **Version your migrations** - Keep migration files in sync with code
5. **Document breaking changes** - Note what data will be lost
6. **Use staging environment** - Test reverts on staging first

## Troubleshooting

### Issue: "Table doesn't exist" after revert

**Problem:** Old code expects table that doesn't exist in database

**Solution:**
- Rollback migrations to match old code
- Or update old code to handle missing table

### Issue: "Column doesn't exist" after revert

**Problem:** Database has new column, old code doesn't know about it

**Solution:**
```python
# In old model, make field optional
field_name = models.CharField(max_length=100, blank=True, null=True)
```

### Issue: Migration state mismatch

**Problem:** `django_migrations` table says migrations are applied, but code doesn't match

**Solution:**
```python
# Check migration state
python manage.py showmigrations

# Fake rollback (mark as unapplied without changing DB)
python manage.py migrate people 0020 --fake

# Then actually rollback
python manage.py migrate people 0019
```

## Quick Decision Tree

```
Want to revert code?
│
├─ Does old code change database schema?
│  │
│  ├─ YES → Must rollback migrations (data loss risk)
│  │   └─ Backup first! → Revert code → Rollback migrations → Deploy
│  │
│  └─ NO → Safe to revert
│      └─ Revert code → Deploy (no migration changes needed)
│
└─ Want to keep current database?
   └─ Update old code to be compatible with current schema
```

## Summary

**Reverting code versions CAN affect your database if:**
- The old code expects a different database schema
- Migrations are out of sync
- You don't rollback migrations to match

**To revert safely:**
1. ✅ Backup database first
2. ✅ Revert code
3. ✅ Rollback migrations to match (if needed)
4. ✅ Test locally
5. ✅ Deploy to Railway

**Remember:** Your PostgreSQL database is separate from your code. Reverting code doesn't automatically revert the database - you need to handle migrations manually.

