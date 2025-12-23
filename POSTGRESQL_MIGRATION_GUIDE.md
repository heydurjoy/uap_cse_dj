# PostgreSQL Migration Guide

This guide will help you migrate your Django site from SQLite to PostgreSQL on Railway, preserving all your existing data.

## Overview

Your site currently uses SQLite, which stores data in a file (`db.sqlite3`). Railway's filesystem is ephemeral, meaning each deployment creates a fresh filesystem, causing data loss. PostgreSQL is a persistent database service that Railway provides, ensuring your data survives deployments.

## Prerequisites

- Your Railway project is already set up
- You have access to your Railway dashboard
- You have important data in your current live database that needs to be preserved

## Step 1: Export Data from Current SQLite Database

Before switching to PostgreSQL, you need to export your current data. You have two options:

### Option A: Export from Live Site (Recommended if you have SSH/CLI access)

If you can access your Railway service via CLI or SSH:

1. Connect to your Railway service
2. Run the following command to export all data:
   ```bash
   python manage.py dumpdata --exclude auth.permission --exclude contenttypes > data_dump.json
   ```
   Note: We exclude `auth.permission` and `contenttypes` as these are auto-generated and will be recreated during migration.

3. Download the `data_dump.json` file to your local machine

### Option B: Export from Local SQLite Database (If you have a recent backup)

If you have a local copy of your database:

1. Make sure your local `db.sqlite3` is up to date
2. Run:
   ```bash
   python manage.py dumpdata --exclude auth.permission --exclude contenttypes > data_dump.json
   ```

### Option C: Manual Export via Django Admin (If CLI access is not available)

If you cannot access the CLI, you can manually export data through Django admin:

1. Log into your Django admin panel
2. For each model, use the "Export" functionality if available
3. Or manually copy important data that you need to preserve

**Important**: Save the exported data file (`data_dump.json`) in a safe location. You'll need it in Step 4.

## Step 2: Add PostgreSQL Service to Railway

1. Go to your Railway project dashboard
2. Click **"+ New"** button
3. Select **"Database"** → **"Add PostgreSQL"**
4. Railway will automatically create a PostgreSQL database service
5. Railway will automatically provide a `DATABASE_URL` environment variable to your Django service

**Note**: Railway automatically links the PostgreSQL service to your Django service and sets the `DATABASE_URL` environment variable. No manual configuration needed!

## Step 3: Deploy Your Updated Code

1. Commit and push your changes to GitHub:
   ```bash
   git add .
   git commit -m "Migrate to PostgreSQL for persistent data storage"
   git push origin main
   ```

2. Railway will automatically detect the push and start a new deployment
3. The deployment will:
   - Install `psycopg2-binary` and `dj-database-url` packages
   - Run `collectstatic` to gather static files
   - Run `migrate` to create database tables in PostgreSQL
4. Wait for the deployment to complete

## Step 4: Import Your Data into PostgreSQL

After the deployment completes and migrations have run:

### Option A: Using Railway CLI

1. Connect to your Railway service via CLI
2. Run:
   ```bash
   python manage.py loaddata data_dump.json
   ```

### Option B: Using Local Django with Remote Database

1. Get your PostgreSQL connection string from Railway dashboard:
   - Go to your PostgreSQL service
   - Click on the "Variables" tab
   - Copy the `DATABASE_URL` value

2. Set it temporarily in your local environment:
   ```bash
   # Windows PowerShell
   $env:DATABASE_URL="your-database-url-here"
   
   # Windows CMD
   set DATABASE_URL=your-database-url-here
   
   # Linux/Mac
   export DATABASE_URL="your-database-url-here"
   ```

3. Run the loaddata command:
   ```bash
   python manage.py loaddata data_dump.json
   ```

4. Remove the environment variable after import:
   ```bash
   # Windows PowerShell
   Remove-Item Env:\DATABASE_URL
   ```

### Option C: Using Django Admin (Manual Import)

If automated import doesn't work, you can manually recreate important data through the Django admin interface.

## Step 5: Verify the Migration

1. Visit your live site
2. Check that:
   - All users can log in
   - All content (posts, courses, etc.) is visible
   - Admin panel works correctly
3. Test creating new data to ensure the database is working

## Step 6: Clean Up (Optional)

After confirming everything works:

1. You can remove the `data_dump.json` file (or keep it as a backup)
2. Your local `db.sqlite3` will continue to work for local development
3. Production will now use PostgreSQL and persist data across deployments

## Troubleshooting

### Issue: Migration fails with "relation already exists"

**Solution**: This means tables already exist. You can either:
- Drop and recreate the database (loses data, only do this if you haven't imported data yet)
- Or skip the migration step if tables are already created

### Issue: Data import fails with foreign key errors

**Solution**: The dump might have dependency issues. Try:
```bash
python manage.py loaddata data_dump.json --ignorenonexistent
```

### Issue: Can't connect to PostgreSQL

**Solution**: 
- Verify `DATABASE_URL` is set in Railway environment variables
- Check that PostgreSQL service is running
- Ensure the services are linked in Railway dashboard

### Issue: Local development still uses SQLite

**Solution**: This is correct! Local development uses SQLite (no `DATABASE_URL` set), and production uses PostgreSQL. This is the intended behavior.

## Future Deployments

After this migration:
- ✅ All data will persist across deployments
- ✅ You can push code changes without losing data
- ✅ PostgreSQL is a production-grade database suitable for your growing site
- ✅ Local development continues using SQLite (no changes needed)

## Need Help?

If you encounter issues:
1. Check Railway deployment logs
2. Check Railway service logs for Django errors
3. Verify environment variables are set correctly
4. Ensure PostgreSQL service is running and linked to your Django service

