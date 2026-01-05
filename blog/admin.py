from django.contrib import admin
from .models import User, Post, Comment, Like, Follow, Category, RestoreRequest


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'date_joined']
    list_filter = ['role']
    search_fields = ['username', 'email']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'content']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at', 'is_reply']
    list_filter = ['created_at']


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'followed_author', 'created_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']


@admin.register(RestoreRequest)
class RestoreRequestAdmin(admin.ModelAdmin):
    list_display = ['post', 'writer', 'status', 'created_at', 'reviewed_at', 'reviewed_by']
    list_filter = ['status', 'created_at']
    search_fields = ['post__title', 'writer__username']
    readonly_fields = ['created_at', 'reviewed_at']

