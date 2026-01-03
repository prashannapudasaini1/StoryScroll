from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator


class User(AbstractUser):
    """Custom User model with role-based access control
    
    Note: Django's AbstractUser uses Django's built-in password hashing system
    which is more secure than Werkzeug. The password field is automatically
    hashed when using user.set_password() and checked with user.check_password().
    """
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Writer', 'Writer'),
        ('Reader', 'Reader'),
    ]
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
        ('Prefer not to say', 'Prefer not to say'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Reader')
    middle_name = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    # Approval system
    is_approved = models.BooleanField(default=False)  # For Reader approval by Admin
    writer_request = models.BooleanField(default=False)  # Reader requesting to become Writer
    writer_request_message = models.TextField(blank=True, null=True)  # Optional message for writer request
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def get_full_name_with_middle(self):
        """Get full name including middle name"""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return ' '.join(filter(None, parts))


class Post(models.Model):
    """Blog post model"""
    CATEGORY_CHOICES = [
        ('Technology', 'Technology'),
        ('Lifestyle', 'Lifestyle'),
        ('Travel', 'Travel'),
        ('Food', 'Food'),
        ('Fashion', 'Fashion'),
        ('Health', 'Health'),
        ('Education', 'Education'),
        ('Business', 'Business'),
        ('Entertainment', 'Entertainment'),
        ('Other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Other')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    featured_image = models.ImageField(
        upload_to='post_images/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_like_count(self):
        """Get total number of likes for this post"""
        return self.likes.count()
    
    def is_liked_by(self, user):
        """Check if post is liked by a specific user"""
        if not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()


class Comment(models.Model):
    """Comment model with support for replies"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"
    
    def is_reply(self):
        """Check if this comment is a reply"""
        return self.parent is not None


class Like(models.Model):
    """Like model for posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'user']  # Prevent duplicate likes
    
    def __str__(self):
        return f"{self.user.username} liked {self.post.title}"


class Follow(models.Model):
    """Follow model for following authors"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed_author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'followed_author']  # Prevent duplicate follows
    
    def __str__(self):
        return f"{self.follower.username} follows {self.followed_author.username}"

