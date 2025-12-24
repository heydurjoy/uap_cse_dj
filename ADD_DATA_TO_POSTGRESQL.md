# Adding Data to PostgreSQL Database on Railway

This guide shows you various ways to add/insert data into your PostgreSQL database on Railway.

## Prerequisites

- You have created a superuser (already done ✅)
- You have the public `DATABASE_URL` connection string
- Your Django project is set up

## Method 1: Using Django Shell (Recommended)

Django shell lets you interact with your database using Python and the Django ORM.

### Step 1: Connect to Database

Set your DATABASE_URL and open Django shell:

**Windows PowerShell:**
```powershell
$env:DATABASE_URL="postgresql://postgres:BDGvLvKHzWtIZJATrTwmzbgkZrvLQloV@metro.proxy.rlwy.net:25027/railway"
python manage.py shell
```

### Step 2: Create Objects in Shell

Once in the shell, you can create any model instance:

```python
# Import your models
from people.models import BaseUser, Faculty, Staff, Officer, ClubMember, AllowedEmail
from clubs.models import Club, ClubPost
from academics.models import Course
from office.models import UAPNowPost

# Example 1: Create a new user
user = BaseUser.objects.create_user(
    username='john_doe',
    email='john@example.com',
    password='secure_password123',
    user_type='faculty',
    is_power_user=True
)

# Example 2: Create a Faculty member
faculty = Faculty.objects.create(
    base_user=user,
    name='Dr. John Doe',
    designation='Professor',
    department='CSE',
    email='john@example.com'
)

# Example 3: Create a Club
from clubs.models import Club
club = Club.objects.create(
    name='Programming Club',
    short_name='PC',
    moto='Code, Learn, Grow',
    description='A club for programming enthusiasts'
)

# Example 4: Create a Club Post
from clubs.models import ClubPost
post = ClubPost.objects.create(
    club=club,
    title='Welcome to Programming Club',
    content='This is our first post!',
    posted_by=user,
    posted_by_name='John Doe',
    posted_by_email='john@example.com'
)

# Example 5: Create an AllowedEmail
allowed_email = AllowedEmail.objects.create(
    email='newuser@example.com',
    user_type='faculty',
    is_power_user=False
)

# Save changes (usually automatic, but explicit for clarity)
user.save()
faculty.save()
club.save()
post.save()
allowed_email.save()

# Exit shell
exit()
```

### Step 3: Exit and Clean Up

```python
exit()  # Exit Django shell
```

Then remove the environment variable:
```powershell
Remove-Item Env:\DATABASE_URL
```

## Method 2: Using Django Admin Interface

The easiest visual method - use the web interface.

### Step 1: Access Admin Panel

1. Go to: `https://your-railway-app.railway.app/admin/`
2. Log in with your superuser credentials

### Step 2: Add Objects

1. Navigate to the model you want to add (e.g., "People" → "Base Users")
2. Click "Add [Model Name]" button
3. Fill in the form fields
4. Click "Save"

**Note:** Make sure your models are registered in `admin.py` files for them to appear in admin.

## Method 3: Using Management Commands

Create custom management commands for bulk operations.

### Example: Create a Management Command

Create a file: `people/management/commands/create_sample_data.py`

```python
from django.core.management.base import BaseCommand
from people.models import BaseUser, Faculty

class Command(BaseCommand):
    help = 'Creates sample data'

    def handle(self, *args, **options):
        # Create a user
        user = BaseUser.objects.create_user(
            username='sample_user',
            email='sample@example.com',
            password='password123'
        )
        
        # Create faculty
        faculty = Faculty.objects.create(
            base_user=user,
            name='Sample Faculty',
            designation='Assistant Professor',
            department='CSE'
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {user.username}')
        )
```

Then run:
```powershell
$env:DATABASE_URL="postgresql://postgres:BDGvLvKHzWtIZJATrTwmzbgkZrvLQloV@metro.proxy.rlwy.net:25027/railway"
python manage.py create_sample_data
```

## Method 4: Using Fixtures (JSON/XML/YAML)

Good for importing existing data or bulk inserts.

### Step 1: Create a Fixture File

Create `fixtures/sample_data.json`:

```json
[
  {
    "model": "people.baseuser",
    "pk": 1,
    "fields": {
      "username": "test_user",
      "email": "test@example.com",
      "user_type": "faculty",
      "is_active": true
    }
  },
  {
    "model": "clubs.club",
    "pk": 1,
    "fields": {
      "name": "Test Club",
      "short_name": "TC",
      "moto": "Test Motto"
    }
  }
]
```

### Step 2: Load the Fixture

```powershell
$env:DATABASE_URL="postgresql://postgres:BDGvLvKHzWtIZJATrTwmzbgkZrvLQloV@metro.proxy.rlwy.net:25027/railway"
python manage.py loaddata fixtures/sample_data.json
```

## Method 5: Direct SQL Queries

Use raw SQL for complex operations or when ORM is not suitable.

### Option A: Using Django's Database Connection

```python
from django.db import connection

# In Django shell
with connection.cursor() as cursor:
    cursor.execute("""
        INSERT INTO people_baseuser (username, email, password, is_active, is_staff, is_superuser, date_joined)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
    """, ['newuser', 'newuser@example.com', 'hashed_password', True, False, False])
```

**Note:** For passwords, you should use Django's password hashing:
```python
from django.contrib.auth.hashers import make_password
hashed = make_password('plain_password')
```

### Option B: Using psql (PostgreSQL CLI)

Connect directly to PostgreSQL:

```powershell
# Install psql if not available (usually comes with PostgreSQL)
# Or use Railway's connection string

psql "postgresql://postgres:BDGvLvKHzWtIZJATrTwmzbgkZrvLQloV@metro.proxy.rlwy.net:25027/railway"
```

Then run SQL:
```sql
INSERT INTO people_baseuser (username, email, password, is_active, is_staff, is_superuser, date_joined)
VALUES ('newuser', 'newuser@example.com', 'hashed_password', true, false, false, NOW());
```

**⚠️ Warning:** Direct SQL bypasses Django's validation and signals. Use with caution!

## Method 6: Using Railway Web Shell

Run commands directly on Railway's server.

1. Go to Railway dashboard → Django service → Deployments → Latest → Shell
2. Run Django shell:
   ```bash
   python manage.py shell
   ```
3. Use the same Python code as Method 1

## Common Examples by Model

### Creating a BaseUser

```python
from people.models import BaseUser

user = BaseUser.objects.create_user(
    username='username',
    email='email@example.com',
    password='password',
    user_type='faculty',  # or 'staff', 'officer', 'club_member'
    is_power_user=True,   # optional
    phone_number='+1234567890'  # optional
)
```

### Creating a Faculty Member

```python
from people.models import BaseUser, Faculty

# First create the user
user = BaseUser.objects.create_user(
    username='faculty1',
    email='faculty@example.com',
    password='password',
    user_type='faculty'
)

# Then create the faculty profile
faculty = Faculty.objects.create(
    base_user=user,
    name='Dr. Faculty Name',
    designation='Professor',
    department='CSE',
    email='faculty@example.com',
    bio='Faculty bio here'
)
```

### Creating a Club

```python
from clubs.models import Club
from people.models import Faculty

# Get or create a faculty convener (optional)
convener = Faculty.objects.first()

club = Club.objects.create(
    name='Programming Club',
    short_name='PC',
    sl=1,
    moto='Code, Learn, Grow',
    description='A club for programming enthusiasts',
    convener=convener  # optional
)
```

### Creating a Club Post

```python
from clubs.models import Club, ClubPost
from people.models import BaseUser

club = Club.objects.get(name='Programming Club')
user = BaseUser.objects.get(username='admin')

post = ClubPost.objects.create(
    club=club,
    title='Welcome Post',
    content='This is the content of the post',
    posted_by=user,
    posted_by_name='Admin User',
    posted_by_email='admin@example.com',
    is_pinned=False
)
```

### Creating a Course

```python
from academics.models import Course

course = Course.objects.create(
    course_code='CSE101',
    course_title='Introduction to Programming',
    credit_hours=3.0,
    course_type='Theory',
    description='Basic programming concepts'
)
```

## Bulk Operations

### Bulk Create (Efficient for many objects)

```python
from people.models import BaseUser

users = [
    BaseUser(username=f'user{i}', email=f'user{i}@example.com')
    for i in range(100)
]

# Create all at once (more efficient)
BaseUser.objects.bulk_create(users)
```

### Update Multiple Objects

```python
# Update all faculty members
Faculty.objects.filter(department='CSE').update(department='Computer Science')
```

## Best Practices

1. **Use Django ORM** - It handles validation, relationships, and signals
2. **Use transactions** - For multiple related operations:
   ```python
   from django.db import transaction
   
   with transaction.atomic():
       user = BaseUser.objects.create_user(...)
       faculty = Faculty.objects.create(base_user=user, ...)
   ```
3. **Handle errors** - Always check for existing objects:
   ```python
   user, created = BaseUser.objects.get_or_create(
       username='john',
       defaults={'email': 'john@example.com', 'password': 'pass'}
   )
   ```
4. **Use signals** - Django signals can automatically handle related operations
5. **Validate data** - Let Django's validation catch errors before saving

## Troubleshooting

### Issue: Foreign key constraint errors

**Solution:** Make sure referenced objects exist first:
```python
# Wrong - user doesn't exist yet
faculty = Faculty.objects.create(base_user_id=999, ...)

# Correct - create user first
user = BaseUser.objects.create_user(...)
faculty = Faculty.objects.create(base_user=user, ...)
```

### Issue: Unique constraint violations

**Solution:** Use `get_or_create`:
```python
user, created = BaseUser.objects.get_or_create(
    username='john',
    defaults={'email': 'john@example.com', 'password': 'pass'}
)
```

### Issue: Password not hashed

**Solution:** Always use `create_user()` or `set_password()`:
```python
# Wrong
user.password = 'plaintext'

# Correct
user.set_password('plaintext')
user.save()
```

## Security Notes

- **Never commit passwords** to version control
- **Use environment variables** for sensitive data
- **Hash passwords** properly (Django does this automatically)
- **Validate input** before saving to database
- **Use transactions** for critical operations

## Need Help?

If you encounter issues:
1. Check Railway logs for errors
2. Verify DATABASE_URL is correct
3. Ensure migrations are up to date: `python manage.py migrate`
4. Check model relationships and foreign keys
5. Use Django's `full_clean()` to validate before saving

