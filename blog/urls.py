from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/writer/', views.register_writer, name='register_writer'),
    path('register/reader/', views.register_reader, name='register_reader'),
    
    # Profile routes
    path('profile/', views.profile, name='profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/request-writer/', views.request_writer, name='request_writer'),
    
    # Admin routes (using 'system' prefix to avoid conflict with Django admin)
    path('system/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('system/manage/users/', views.admin_manage_users, name='admin_manage_users'),
    path('system/manage/posts/', views.admin_manage_posts, name='admin_manage_posts'),
    path('system/manage/categories/', views.admin_manage_categories, name='admin_manage_categories'),
    path('system/manage/create-admin/', views.admin_create_admin_page, name='admin_create_admin_page'),
    path('system/manage/restore/', views.admin_restore_deleted, name='admin_restore_deleted'),
    path('system/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('system/delete-post/<int:post_id>/', views.delete_post_admin, name='delete_post_admin'),
    path('system/approve-writer/<int:user_id>/', views.approve_writer, name='approve_writer'),
    path('system/approve-writer-request/<int:user_id>/', views.approve_writer_request, name='approve_writer_request'),
    path('system/reject-writer-request/<int:user_id>/', views.reject_writer_request, name='reject_writer_request'),
    path('system/create-admin/', views.create_admin, name='create_admin'),
    path('system/add-category/', views.add_category, name='add_category'),
    path('system/delete-category/<int:category_id>/', views.delete_category, name='delete_category'),
    path('system/restore-user/<int:user_id>/', views.restore_user, name='restore_user'),
    path('system/restore-post/<int:post_id>/', views.restore_post, name='restore_post'),
    path('system/restore-category/<int:category_id>/', views.restore_category, name='restore_category'),
    path('system/approve-restore-request/<int:request_id>/', views.approve_restore_request, name='approve_restore_request'),
    path('system/reject-restore-request/<int:request_id>/', views.reject_restore_request, name='reject_restore_request'),
    
    # Writer routes
    path('writer/dashboard/', views.writer_dashboard, name='writer_dashboard'),
    path('writer/create-post/', views.create_post, name='create_post'),
    path('writer/edit-post/<int:post_id>/', views.edit_post, name='edit_post'),
    path('writer/delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('writer/request-restore/<int:post_id>/', views.request_restore_post, name='request_restore_post'),
    path('writer/post/<int:post_id>/comments/', views.view_post_comments, name='view_post_comments'),
    path('writer/reply-comment/<int:comment_id>/', views.reply_comment, name='reply_comment'),
    
    # Reader routes
    path('reader/dashboard/', views.reader_dashboard, name='reader_dashboard'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('author/<int:author_id>/follow/', views.toggle_follow, name='toggle_follow'),
    
    # Public routes
    path('authors/ranking/', views.author_ranking, name='author_ranking'),
    
    # Home redirect
    path('', views.login_view, name='home'),
]


