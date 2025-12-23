# pgAdmin Setup Guide for Railway PostgreSQL

This guide shows you how to connect pgAdmin to your Railway PostgreSQL database.

## Prerequisites

1. You have added a PostgreSQL service to your Railway project
2. pgAdmin is installed and running on your computer

## Step 1: Get Connection Details from Railway

1. Go to your **Railway dashboard**
2. Click on your **PostgreSQL service** (not your Django app)
3. Go to the **"Variables"** tab
4. You'll see these connection details:
   - `PGHOST` - Host address
   - `PGPORT` - Port (usually 5432)
   - `PGDATABASE` - Database name
   - `PGUSER` - Username
   - `PGPASSWORD` - Password
   - `DATABASE_URL` - Full connection string

**Important**: Copy these values - you'll need them for pgAdmin.

## Step 2: Connect pgAdmin to Railway PostgreSQL

### Option A: Using Connection String (Easiest)

1. Open **pgAdmin**
2. Right-click on **"Servers"** in the left panel
3. Select **"Register" → "Server"**
4. In the **"General"** tab:
   - **Name**: `Railway PostgreSQL` (or any name you prefer)
5. Go to the **"Connection"** tab:
   - **Host name/address**: Copy from `PGHOST` (e.g., `containers-us-west-xxx.railway.app`)
   - **Port**: Copy from `PGPORT` (usually `5432`)
   - **Maintenance database**: Copy from `PGDATABASE`
   - **Username**: Copy from `PGUSER`
   - **Password**: Copy from `PGPASSWORD`
   - ✅ Check **"Save password"** (optional, for convenience)
6. Go to the **"SSL"** tab:
   - **SSL mode**: Select **"Require"** or **"Prefer"**
   - Railway PostgreSQL uses SSL by default
7. Click **"Save"**

### Option B: Parse DATABASE_URL (If individual values aren't shown)

If Railway only shows `DATABASE_URL`, it looks like:
```
postgresql://user:password@host:port/database
```

Parse it:
- **Host**: Part after `@` and before `:`
- **Port**: Number after the host `:`
- **Database**: Part after the last `/`
- **Username**: Part after `postgresql://` and before `:`
- **Password**: Part after username `:` and before `@`

## Step 3: Verify Connection

1. After saving, pgAdmin will try to connect
2. If successful, you'll see your database appear under the server
3. You can expand it to see:
   - **Schemas** → **public** → **Tables** (after migrations run)
   - **Tables** will show all your Django models

## Step 4: View Your Django Tables

After your Django migrations run, you'll see tables like:
- `people_baseuser`
- `academics_course`
- `clubs_clubpost`
- `django_migrations`
- etc.

## Troubleshooting

### Connection Refused / Timeout

**Problem**: Can't connect to Railway PostgreSQL

**Solutions**:
1. **Check Railway service is running**: Make sure PostgreSQL service is active in Railway
2. **Verify connection details**: Double-check all values are correct
3. **Check SSL mode**: Try "Prefer" instead of "Require"
4. **Firewall/Network**: Some networks block database connections - try different network

### Authentication Failed

**Problem**: Wrong username/password

**Solutions**:
1. **Regenerate password**: In Railway, go to PostgreSQL service → Variables → Regenerate password
2. **Copy exact values**: Make sure no extra spaces when copying
3. **Check DATABASE_URL**: If using DATABASE_URL, parse it carefully

### SSL Connection Required

**Problem**: SSL error

**Solutions**:
1. Set **SSL mode** to **"Require"** or **"Prefer"** in pgAdmin
2. Railway PostgreSQL requires SSL connections

## Using pgAdmin with Your Django Project

Once connected, you can:

1. **View data**: Browse tables and see your data
2. **Run queries**: Execute SQL queries directly
3. **Export data**: Right-click table → "Backup" to export
4. **Import data**: Right-click database → "Restore" to import
5. **Monitor**: Check database size, connections, etc.

## Important Notes

- **Read-only recommended**: Be careful with writes - changes affect production!
- **Backup first**: Always backup before making changes
- **Use Django admin**: For data changes, prefer Django admin over direct SQL
- **Connection limits**: Railway has connection limits on free tier

## Alternative: Railway's Built-in Database Viewer

Railway also provides a web-based database viewer:
1. Go to PostgreSQL service in Railway
2. Click **"Data"** or **"Query"** tab
3. View and query your database directly in the browser

This is simpler but less powerful than pgAdmin.

