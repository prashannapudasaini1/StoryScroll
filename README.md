# StoryScroll Blogging Platform

A multi-user blogging platform built with Django, PostgreSQL, and Bootstrap 5, featuring role-based access control (Admin, Writer, Reader).

## Features

- **Role-Based Access Control**: Three distinct user roles (Admin, Writer, Reader) with different permissions
- **Unified Login System**: Single login page with automatic role-based redirection
- **Blog Management**: Writers can create, edit, and delete their own posts
- **Social Features**: Readers can like posts, comment, and follow authors
- **Author Ranking**: Leaderboard showing authors ranked by follower count
- **Modern UI**: Clean, responsive design using Bootstrap 5

## Tech Stack

- **Backend**: Python (Django 4.2)
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Database**: PostgreSQL
- **Authentication**: Django's session-based authentication with custom role system

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL
- pip

### Setup Steps

1. **Clone the repository** (if applicable) or navigate to the project directory:
   ```bash
   cd /home/prashanna/Desktop/story
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**:
   - Create a PostgreSQL database named `storyscroll_db`
   - Update database credentials in `storyscroll/settings.py` if needed:
     ```python
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.postgresql',
             'NAME': 'storyscroll_db',
             'USER': 'postgres',
             'PASSWORD': 'postgres',
             'HOST': 'localhost',
             'PORT': '5432',
         }
     }
     ```

5. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser** (Admin account):
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to create an admin user. You can set the role to 'Admin' in the Django admin panel.

7. **Create additional users** (optional):
   - Use Django admin panel at `/admin/` to create Writer and Reader accounts
   - Or create them programmatically using Django shell

8. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

9. **Access the application**:
   - Open your browser and navigate to `http://127.0.0.1:8000/`
   - Login with your credentials

## User Roles & Permissions

### Admin
- Full access to System Dashboard
- Can delete any user account (Reader or Writer)
- Can delete any blog post that violates terms
- Access: `/admin/dashboard/`

### Writer
- Access to Writer Dashboard
- Create, Edit, and Delete their own blog posts
- View "Like" counts on their posts
- Read comments and reply to comments on their own posts
- Access: `/writer/dashboard/`

### Reader
- Access to Reader Dashboard
- Read all blog posts
- Like posts and write new comments
- Follow/Unfollow Authors
- Filter posts by category, author, or followed authors
- Access: `/reader/dashboard/`

## Database Schema

The application uses the following models:

- **User**: Custom user model with role, bio, and profile_pic fields
- **Post**: Blog posts with title, content, author, category, and featured_image
- **Comment**: Comments with support for nested replies (parent_id)
- **Like**: Tracks likes on posts (unique per user-post combination)
- **Follow**: Tracks follower relationships (unique per follower-followed_author combination)

## Key Routes

- `/` or `/login/` - Login page
- `/admin/dashboard/` - Admin dashboard
- `/writer/dashboard/` - Writer dashboard
- `/reader/dashboard/` - Reader dashboard
- `/authors/ranking/` - Author ranking page
- `/post/<id>/` - View individual post
- `/writer/create-post/` - Create new post
- `/writer/edit-post/<id>/` - Edit post

## Project Structure

```
story/
├── manage.py
├── requirements.txt
├── README.md
├── storyscroll/          # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── blog/                 # Main application
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── decorators.py
    └── templates/
        └── blog/
            ├── base.html
            ├── login.html
            ├── admin_dashboard.html
            ├── writer_dashboard.html
            ├── reader_dashboard.html
            ├── create_post.html
            ├── edit_post.html
            ├── post_detail.html
            ├── view_comments.html
            └── author_ranking.html
```

## Security Features

- Role-based route protection using custom decorators
- CSRF protection on all forms
- Session-based authentication
- Unique constraints on Like and Follow models to prevent duplicates

## Notes

- Django's built-in password hashing is used (more secure than Werkzeug and integrates better with Django's authentication system)
- Media files (images) are stored in the `media/` directory
- Static files should be collected using `python manage.py collectstatic` for production

## Development

To create test users with different roles, you can use Django shell:

```python
python manage.py shell

from blog.models import User

# Create a Writer
writer = User.objects.create_user(username='writer1', email='writer@example.com', password='password123', role='Writer')

# Create a Reader
reader = User.objects.create_user(username='reader1', email='reader@example.com', password='password123', role='Reader')
```

## License

This project is created for educational purposes.


