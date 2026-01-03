#!/bin/bash

# StoryScroll Setup Script
echo "Setting up StoryScroll Blogging Platform..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check PostgreSQL connection
echo "Checking PostgreSQL connection..."
echo "Please ensure PostgreSQL is running and the database 'storyscroll_db' exists."
echo "You can create it with: createdb storyscroll_db"

# Run migrations
echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser
echo ""
echo "Creating superuser (Admin account)..."
echo "Please follow the prompts to create an admin user."
python manage.py createsuperuser

echo ""
echo "Setup complete!"
echo ""
echo "To run the server:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "Then visit http://127.0.0.1:8000/ in your browser"


