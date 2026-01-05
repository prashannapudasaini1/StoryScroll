# StoryScroll - Blog Platform

StoryScroll is a comprehensive blog platform built with Django that supports multiple user roles (Admin, Writer, Reader) with role-based access control, content management, and social features.

## Features

### User Roles
- **Admin**: Full system access including user management, post moderation, category management, and creating new admin accounts
- **Writer**: Create, edit, and manage blog posts. Writers require admin approval upon registration
- **Reader**: Read posts, like, comment, and follow writers. Readers are auto-approved upon registration

### Core Functionality
- **User Registration & Authentication**: Role-based registration with email/username login
- **Profile Management**: Users can upload profile pictures and update their profile information
- **Blog Post Management**: Writers can create, edit, and delete posts with categories and featured images
- **Search & Filter**: Advanced search by post title, author name, and category
- **Social Features**: 
  - Like posts
  - Comment on posts with reply support
  - Follow/unfollow writers
  - Author ranking based on followers
- **Category Management**: Dynamic category system managed by admins
- **Soft Delete**: Deleted items are preserved in the database and can be restored
- **Admin Dashboard**: Comprehensive dashboard for managing users, posts, categories, and approvals

## Technology Stack

- **Backend**: Django (Python)
- **Database**: SQLite (default, can be configured for PostgreSQL/MySQL)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Icons**: Bootstrap Icons

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd StoryScroll
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser (Admin account)**
   ```bash
   python manage.py createsuperuser_with_role
   ```
   Or use the standard Django command:
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open your browser and navigate to: `http://127.0.0.1:8000/`
   - Login with your admin credentials

## Project Structure

```
StoryScroll/
├── blog/                    # Main application
│   ├── models.py           # Database models (User, Post, Category, Comment, Like, Follow)
│   ├── views.py            # View functions and business logic
│   ├── urls.py             # URL routing
│   ├── forms.py            # Form definitions
│   ├── admin.py            # Django admin configuration
│   ├── decorators.py       # Custom decorators (role_required)
│   ├── utils.py            # Utility functions
│   ├── templates/          # HTML templates
│   │   └── blog/
│   │       ├── base.html
│   │       ├── login.html
│   │       ├── register.html
│   │       ├── profile.html
│   │       ├── admin_dashboard.html
│   │       ├── writer_dashboard.html
│   │       ├── reader_dashboard.html
│   │       └── ...
│   └── migrations/         # Database migrations
├── storyscroll/            # Django project settings
│   ├── settings.py         # Project settings
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py            # WSGI configuration
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## User Guide

### For Readers
1. **Register**: Click "Create one here" on the login page and register as a Reader
2. **Browse Posts**: View all posts on the reader dashboard
3. **Search**: Use the search bar to find posts by title, author, or category
4. **Filter**: Filter posts by category or follow specific authors
5. **Interact**: Like posts, add comments, and follow your favorite writers
6. **Profile**: Upload a profile picture and update your information

### For Writers
1. **Register**: Register as a Writer (requires admin approval)
2. **Wait for Approval**: Admin will approve your account
3. **Create Posts**: Once approved, create and publish blog posts
4. **Manage Content**: Edit or delete your posts from the writer dashboard
5. **Engage**: Reply to comments on your posts

### For Admins
1. **Dashboard**: Access the admin dashboard to manage the platform
2. **Approve Writers**: Review and approve pending writer registrations
3. **Manage Users**: View all users and delete accounts if needed
4. **Manage Posts**: View all posts and delete inappropriate content
5. **Category Management**: Add or delete categories
6. **Create Admins**: Create new admin accounts
7. **Restore Items**: Restore deleted users, posts, or categories

## Key Features Explained

### Soft Delete System
- When items are deleted, they are marked as `is_deleted=True` instead of being permanently removed
- Deleted items can be viewed and restored from the admin dashboard
- Regular queries automatically exclude deleted items

### Search Functionality
- Search by post title
- Search by author name (username, first name, last name)
- Search by category name
- Combined search across all fields

### Profile Pictures
- Users can upload profile pictures from their profile page
- Profile pictures are displayed on:
  - User profile page
  - Post author information
  - Comment author information
  - Admin dashboard (pending approvals)
  - Author ranking page

### Dynamic Categories
- Admins can add new categories dynamically
- Categories are stored in the database
- Writers can select from available categories when creating posts

## Database Models

### User
- Custom user model extending Django's AbstractUser
- Fields: role, profile_pic, bio, is_approved, is_deleted, etc.
- Supports soft delete

### Post
- Blog post model with title, content, author, category
- Supports featured images
- Soft delete enabled

### Category
- Dynamic category management
- Name and description fields
- Soft delete enabled

### Comment
- Comments on posts with reply support
- Parent-child relationship for nested comments
- Soft delete enabled

### Like
- Many-to-many relationship between users and posts
- Prevents duplicate likes

### Follow
- Follow relationship between readers and writers
- Used for filtering followed authors' posts

## API Endpoints

### Authentication
- `/login/` - Login page
- `/logout/` - Logout
- `/register/reader/` - Register as Reader
- `/register/writer/` - Register as Writer

### Profile
- `/profile/` - User profile page
- `/profile/change-password/` - Change password
- `/profile/request-writer/` - Request writer role (Readers only)

### Admin
- `/system/dashboard/` - Admin dashboard
- `/system/approve-writer/<id>/` - Approve writer registration
- `/system/create-admin/` - Create new admin account
- `/system/add-category/` - Add new category
- `/system/restore-user/<id>/` - Restore deleted user
- `/system/restore-post/<id>/` - Restore deleted post
- `/system/restore-category/<id>/` - Restore deleted category

### Writer
- `/writer/dashboard/` - Writer dashboard
- `/writer/create-post/` - Create new post
- `/writer/edit-post/<id>/` - Edit post
- `/writer/delete-post/<id>/` - Delete post

### Reader
- `/reader/dashboard/` - Reader dashboard
- `/post/<id>/` - View post details
- `/post/<id>/like/` - Like/unlike post
- `/post/<id>/comment/` - Add comment
- `/author/<id>/follow/` - Follow/unfollow author

## Configuration

### Settings
Main settings are in `storyscroll/settings.py`:
- `AUTH_USER_MODEL = 'blog.User'` - Custom user model
- `MEDIA_URL` and `MEDIA_ROOT` - For file uploads (profile pictures, post images)

### Database
Default database is SQLite. To use PostgreSQL or MySQL, update `DATABASES` in `settings.py`.

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
```

### Applying Migrations
```bash
python manage.py migrate
```

### Creating Superuser
```bash
python manage.py createsuperuser_with_role
```

## Security Features

- Password hashing using Django's built-in system
- CSRF protection on all forms
- Role-based access control
- Soft delete to prevent accidental data loss
- File upload validation (images only)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on the repository.

## Changelog

### Version 1.0
- Initial release
- User registration and authentication
- Role-based access control
- Blog post management
- Search and filter functionality
- Social features (like, comment, follow)
- Admin dashboard
- Profile picture upload
- Soft delete system
- Dynamic category management

---

**Built with ❤️ using Django**
