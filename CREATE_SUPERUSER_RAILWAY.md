# Creating a Django Superuser on Railway PostgreSQL

This guide shows you how to create a Django superuser for your project deployed on Railway with PostgreSQL.

## Prerequisites

- Your Django project is deployed on Railway
- PostgreSQL service is added and linked to your Django service
- You have access to your Railway dashboard

## Method 1: Using Railway CLI (Recommended for Remote Execution)

⚠️ **Note:** `railway run` uses Railway's internal network hostname which may not work from your local machine. If you get a "could not translate host name" error, use **Method 2 (Web Shell)** or **Method 3 (Local with Public URL)** instead.

### Step 1: Install Railway CLI

If you haven't already, install the Railway CLI:

**Windows (PowerShell):**
```powershell
iwr https://railway.app/install.ps1 | iex
```

**Mac/Linux:**
```bash
curl -fsSL https://railway.app/install.sh | sh
```

### Step 2: Login to Railway

```bash
railway login
```

This will open your browser to authenticate.

### Step 3: Link to Your Project

```bash
railway link
```

Select your project when prompted.

### Step 4: Connect to Your Service and Create Superuser

```bash
railway run python manage.py createsuperuser
```

**Note:** If you encounter `could not translate host name "postgres.railway.internal"`, this means Railway CLI is using the internal hostname which doesn't work from your local machine. Use Method 2 or Method 3 instead.

**Example:**
```
$ railway run python manage.py createsuperuser
Username: admin
Email address: admin@example.com
Password: 
Password (again): 
Superuser created successfully.
```

## Method 2: Using Railway Web Shell (Easiest - No Local Setup)

This is the **easiest method** and works reliably because it runs inside Railway's network.

### Step 1: Open Railway Shell

1. Go to your Railway dashboard
2. Click on your **Django service** (not PostgreSQL)
3. Click on the **"Deployments"** tab
4. Click on the latest deployment
5. Click on the **"Shell"** tab (or look for a terminal/shell icon)

### Step 2: Run Createsuperuser Command

In the web shell, run:

```bash
python manage.py createsuperuser
```

Enter the required information when prompted:
- Username
- Email address
- Password (twice)

This method works because the shell runs inside Railway's network and can access the database directly.

## Method 3: Using Local Django with Remote Database (Use Public URL)

You can run the createsuperuser command locally while connected to your Railway PostgreSQL database using the **public** connection string.

### Step 1: Get Public Database Connection String

⚠️ **Important:** Make sure you get the **public** `DATABASE_URL`, not the internal one.

1. Go to your Railway dashboard
2. Click on your **PostgreSQL service** (not Django app)
3. Go to the **"Variables"** tab
4. Look for `DATABASE_URL` - it should have a public hostname like:
   - ✅ `containers-us-west-xxx.railway.app` (public - use this)
   - ❌ `postgres.railway.internal` (internal - won't work locally)

5. Copy the `DATABASE_URL` value that contains the public hostname

**Note:** If you only see an internal URL, Railway may provide a public connection string in a different variable. Check for variables like `PUBLIC_DATABASE_URL` or look in the "Connect" tab of your PostgreSQL service.

### Step 2: Set Environment Variable Locally

**Windows PowerShell:**
```powershell
$env:DATABASE_URL="postgresql://user:password@containers-us-west-xxx.railway.app:5432/railway"
```

**Windows CMD:**
```cmd
set DATABASE_URL=postgresql://user:password@containers-us-west-xxx.railway.app:5432/railway
```

**Linux/Mac:**
```bash
export DATABASE_URL="postgresql://user:password@containers-us-west-xxx.railway.app:5432/railway"
```

### Step 3: Run Createsuperuser

```bash
python manage.py createsuperuser
```

Enter the required information when prompted.

### Step 4: Remove Environment Variable (Optional)

After creating the superuser, you can remove the environment variable:

**Windows PowerShell:**
```powershell
Remove-Item Env:\DATABASE_URL
```

**Windows CMD:**
```cmd
set DATABASE_URL=
```

**Linux/Mac:**
```bash
unset DATABASE_URL
```

## Method 4: Using Django Management Command via Railway Deploy

You can temporarily modify your deployment to run createsuperuser automatically.

### Step 1: Modify railway.toml

Add a command to create superuser (only for first-time setup):

```toml
[deploy]
startCommand = "python manage.py migrate --noinput && python manage.py createsuperuser --noinput --username admin --email admin@example.com || true && gunicorn uap_cse_dj.wsgi:application"
```

**Note:** This method requires setting a password via environment variable, which is less secure. Not recommended for production.

## Method 5: Using psql (PostgreSQL Superuser Only)

⚠️ **Important:** This creates a PostgreSQL superuser, NOT a Django superuser. For Django, you need to use `createsuperuser` command.

If you need a PostgreSQL superuser (for database administration):

### Step 1: Get Connection Details

From Railway PostgreSQL service → Variables tab:
- `PGHOST`
- `PGPORT`
- `PGDATABASE`
- `PGUSER`
- `PGPASSWORD`

### Step 2: Connect via psql

```bash
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE
```

Or using DATABASE_URL:
```bash
psql $DATABASE_URL
```

### Step 3: Create PostgreSQL Superuser

```sql
CREATE USER new_superuser WITH SUPERUSER PASSWORD 'your_password';
```

## Verifying Your Superuser

After creating the superuser, verify it works:

1. Visit your Django admin panel: `https://your-railway-app.railway.app/admin/`
2. Log in with the username and password you created
3. You should see the Django admin interface

## Troubleshooting

### Issue: "createsuperuser" command not found

**Solution:** Make sure you're running the command in the correct directory where `manage.py` is located, or use the full path.

### Issue: Database connection error - "could not translate host name 'postgres.railway.internal'"

**Problem:** Railway CLI is using the internal hostname which doesn't work from your local machine.

**Solutions:**
- **Use Method 2 (Web Shell)** - This runs inside Railway's network and works reliably
- **Use Method 3 with public URL** - Get the public `DATABASE_URL` from Railway dashboard (PostgreSQL service → Variables tab) that has a hostname like `containers-us-west-xxx.railway.app`
- Verify `DATABASE_URL` is set correctly (must use public hostname, not internal)
- Check that PostgreSQL service is running
- Ensure services are linked in Railway dashboard

### Issue: "Superuser already exists"

**Solution:** The superuser already exists. You can:
- Use the existing superuser credentials
- Or reset the password (see below)

### Issue: Forgot superuser password

**Reset password using Railway CLI:**
```bash
railway run python manage.py changepassword <username>
```

Or reset via Django shell:
```bash
railway run python manage.py shell
```

Then in the shell:
```python
from people.models import BaseUser
user = BaseUser.objects.get(username='your_username')
user.set_password('new_password')
user.save()
exit()
```

## Security Best Practices

1. **Use strong passwords** for superuser accounts
2. **Don't commit passwords** to version control
3. **Limit superuser access** - only create when needed
4. **Use environment variables** for sensitive data
5. **Regularly rotate passwords** in production

## Need Help?

If you encounter issues:
1. Check Railway deployment logs
2. Check Railway service logs for Django errors
3. Verify environment variables are set correctly
4. Ensure PostgreSQL service is running and linked

