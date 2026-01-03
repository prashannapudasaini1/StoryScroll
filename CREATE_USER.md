# Creating Users in StoryScroll

## ✅ Database is Ready!

The migrations have been successfully applied. All database tables are created.

## Method 1: Using Custom Command (Recommended)

Use the custom command that handles the role field:

```bash
python manage.py createsuperuser_with_role
```

This will prompt you for:
- Username
- Email (optional)
- Password
- Role (defaults to 'Admin')

Or use with arguments:
```bash
python manage.py createsuperuser_with_role --username admin --email admin@example.com --password yourpassword --role Admin
```

## Method 2: Using Django's Standard Command

Django's standard `createsuperuser` should work now, but it won't set the role field (it will default to 'Reader'):

```bash
python manage.py createsuperuser
```

**After creating the user, you'll need to:**
1. Go to Django admin: http://127.0.0.1:8000/admin/
2. Find your user in the Users section
3. Edit the user and change the role to 'Admin'

## Method 3: Using Django Shell

You can also create users programmatically:

```bash
python manage.py shell
```

Then in the shell:
```python
from blog.models import User

# Create Admin
admin = User.objects.create_user(
    username='admin',
    email='admin@example.com',
    password='yourpassword',
    role='Admin',
    is_staff=True,
    is_superuser=True
)

# Create Writer
writer = User.objects.create_user(
    username='writer1',
    email='writer@example.com',
    password='password123',
    role='Writer'
)

# Create Reader
reader = User.objects.create_user(
    username='reader1',
    email='reader@example.com',
    password='password123',
    role='Reader'
)
```

## Quick Start

Run this command to create an admin user:

```bash
python manage.py createsuperuser_with_role --username admin --email admin@example.com --password admin123 --role Admin
```

Then start the server:
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ and login!

