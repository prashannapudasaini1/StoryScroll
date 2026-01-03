# Database Setup Guide

## Quick Start: Use SQLite (Recommended for Development)

The project is currently configured to use **SQLite** by default, which requires no setup. Just run:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

SQLite is perfect for development and testing. The database file will be created at `db.sqlite3`.

---

## Using PostgreSQL (For Production)

If you want to use PostgreSQL instead, follow these steps:

### Step 1: Install PostgreSQL (if not already installed)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
```

**Windows:**
Download from https://www.postgresql.org/download/windows/

### Step 2: Start PostgreSQL Service

**Linux:**
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS:**
```bash
brew services start postgresql
```

### Step 3: Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt, run:
CREATE DATABASE storyscroll_db;
CREATE USER storyscroll_user WITH PASSWORD 'your_password_here';
ALTER ROLE storyscroll_user SET client_encoding TO 'utf8';
ALTER ROLE storyscroll_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE storyscroll_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE storyscroll_db TO storyscroll_user;
\q
```

### Step 4: Update Django Settings

Edit `storyscroll/settings.py`:

1. **Comment out** the SQLite configuration
2. **Uncomment** the PostgreSQL configuration
3. Update the credentials:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'storyscroll_db',
        'USER': 'storyscroll_user',  # Your PostgreSQL user
        'PASSWORD': 'your_password_here',  # Your PostgreSQL password
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Step 5: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

---

## Using Environment Variables (Recommended for Production)

For better security, use environment variables instead of hardcoding credentials:

1. Create a `.env` file in the project root:
```bash
DB_NAME=storyscroll_db
DB_USER=storyscroll_user
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
```

2. Install python-decouple (optional):
```bash
pip install python-decouple
```

3. Update settings.py to read from environment variables (already configured).

---

## Troubleshooting PostgreSQL Connection Issues

### Error: "password authentication failed"

**Solution 1:** Check if PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

**Solution 2:** Verify your PostgreSQL password:
```bash
sudo -u postgres psql
\password postgres  # Set password for postgres user
```

**Solution 3:** Check PostgreSQL authentication settings:
Edit `/etc/postgresql/*/main/pg_hba.conf` and ensure:
```
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
```

Then restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Error: "database does not exist"

Create the database:
```bash
sudo -u postgres createdb storyscroll_db
```

### Error: "role does not exist"

Create the user:
```bash
sudo -u postgres createuser storyscroll_user
sudo -u postgres psql -c "ALTER USER storyscroll_user WITH PASSWORD 'your_password';"
```

---

## Current Configuration

The project is currently set to use **SQLite** for easy development. To switch to PostgreSQL, follow Step 4 above.

