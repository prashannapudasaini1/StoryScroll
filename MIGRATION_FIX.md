# Migration Fix Instructions

## Problem
The `blog_restorerequest` table doesn't exist even though migrations were created.

## Solution

Run these commands in your terminal (Linux):

```bash
cd ~/Documents/StoryScroll
source venv/bin/activate  # Activate your virtual environment

# Step 1: Check if migration file exists
ls -la blog/migrations/

# Step 2: Create migration for RestoreRequest (if needed)
python3 manage.py makemigrations blog

# Step 3: Check migration status
python3 manage.py showmigrations blog

# Step 4: Apply migrations
python3 manage.py migrate blog

# Step 5: If Step 4 says "No migrations to apply" but table doesn't exist, try:
python3 manage.py migrate blog --fake-initial

# Step 6: If still not working, check the migration file and apply it directly:
python3 manage.py migrate blog 0002_restorerequest  # Replace with actual migration number

# Step 7: Verify table was created
python3 manage.py dbshell
# Then in SQLite shell:
.tables
# You should see blog_restorerequest
.exit
```

## Alternative: Reset Migration (if above doesn't work)

If the migration state is completely out of sync:

```bash
# 1. Delete the problematic migration file (if it exists)
rm blog/migrations/0002_restorerequest.py  # Replace with actual filename

# 2. Create fresh migration
python3 manage.py makemigrations blog

# 3. Apply it
python3 manage.py migrate blog
```

## Quick Fix (Recommended)

Try this first:

```bash
cd ~/Documents/StoryScroll
source venv/bin/activate
python3 manage.py makemigrations blog
python3 manage.py migrate blog
python3 manage.py runserver
```

The error handling I added will prevent the crash, but you still need to apply the migration to use the feature.
