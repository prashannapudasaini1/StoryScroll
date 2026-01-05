from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.cache import cache
from .models import User, Post, Comment, Like, Follow, Category, RestoreRequest
from .decorators import role_required
from .forms import RegistrationForm, CustomPasswordChangeForm, WriterRequestForm
from .utils import generate_unique_username, get_recommended_posts


def login_view(request):
    """Unified login page with role-based redirection (supports email or username)"""
    if request.user.is_authenticated:
        # Redirect based on role
        if request.user.role == 'Admin':
            return redirect('admin_dashboard')
        elif request.user.role == 'Reader':
            return redirect('reader_dashboard')
        else:
            return redirect('writer_dashboard')

    
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try to authenticate with username or email
        user = None
        if '@' in username_or_email:
            # Try email
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        else:
            # Try username
            user = authenticate(request, username=username_or_email, password=password)
        
        if user is not None:
            # Check if Writer is approved
            if user.role == 'Writer' and not user.is_approved:
                messages.warning(request, 'Your writer account is pending admin approval. Please wait for approval.')
                return render(request, 'blog/login.html')
            
            login(request, user)
            # Role-based redirection
            if user.role == 'Admin':
                return redirect('admin_dashboard')
            elif user.role == 'Writer':
                return redirect('writer_dashboard')
            else:
                return redirect('reader_dashboard')
        else:
            messages.error(request, 'Invalid username/email or password.')
    
    return render(request, 'blog/login.html')


def register_writer(request):
    """Registration for Writer (requires admin approval)"""
    if request.user.is_authenticated:
        return redirect('profile')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Auto-generate unique username
            user.username = generate_unique_username(
                form.cleaned_data['first_name'],
                form.cleaned_data['last_name'],
                form.cleaned_data.get('middle_name')
            )
            user.set_password(form.cleaned_data['password'])
            user.role = 'Writer'
            user.is_approved = False  # Writers need admin approval
            user.save()
            messages.success(request, f'Writer account created! Your username is: {user.username}. Please wait for admin approval before you can login.')
            return redirect('login')
    else:
        form = RegistrationForm()
    
    return render(request, 'blog/register.html', {
        'form': form,
        'user_type': 'Writer',
        'title': 'Register as Writer'
    })


def register_reader(request):
    """Registration for Reader (auto-approved)"""
    if request.user.is_authenticated:
        return redirect('profile')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Auto-generate unique username
            user.username = generate_unique_username(
                form.cleaned_data['first_name'],
                form.cleaned_data['last_name'],
                form.cleaned_data.get('middle_name')
            )
            user.set_password(form.cleaned_data['password'])
            user.role = 'Reader'
            user.is_approved = True  # Readers are auto-approved
            user.save()
            messages.success(request, f'Reader account created successfully! Your username is: {user.username}. You can now login.')
            return redirect('login')
    else:
        form = RegistrationForm()
    
    return render(request, 'blog/register.html', {
        'form': form,
        'user_type': 'Reader',
        'title': 'Register as Reader'
    })


def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')




@role_required(['Admin'])
def delete_user(request, user_id):
    """Soft delete a user account (Admin only)"""
    if request.method == 'POST':
        user = get_object_or_404(User.all_objects, id=user_id)
        if user.role == 'Admin' and user != request.user:
            messages.error(request, 'Cannot delete another admin account.')
        elif user.is_deleted:
            messages.warning(request, f'User {user.username} is already deleted.')
        else:
            user.is_deleted = True
            user.deleted_at = timezone.now()
            user.save()
            messages.success(request, f'User {user.username} has been deleted.')
    return redirect('admin_dashboard')


@role_required(['Admin'])
def delete_post_admin(request, post_id):
    """Soft delete any post (Admin only)"""
    if request.method == 'POST':
        post = get_object_or_404(Post.all_objects, id=post_id)
        if post.is_deleted:
            messages.warning(request, 'Post is already deleted.')
        else:
            post.is_deleted = True
            post.deleted_at = timezone.now()
            post.save()
            messages.success(request, 'Post has been deleted.')
    return redirect('admin_dashboard')


@role_required(['Writer'])
def writer_dashboard(request):
    """Writer dashboard with post management"""
    posts = Post.objects.filter(author=request.user).order_by('-created_at')
    deleted_posts = Post.all_objects.filter(author=request.user, is_deleted=True).order_by('-deleted_at')
    
    # Get pending restore requests for this writer (with error handling for missing table)
    try:
        pending_restore_requests = RestoreRequest.objects.filter(
            writer=request.user, 
            status='Pending'
        ).values_list('post_id', flat=True)
    except Exception:
        # Table doesn't exist yet - migrations not applied
        # This will be resolved once migrations are applied
        pending_restore_requests = []
    
    context = {
        'posts': posts,
        'deleted_posts': deleted_posts,
        'pending_restore_requests': pending_restore_requests,
    }
    return render(request, 'blog/writer_dashboard.html', context)


@role_required(['Writer'])
def create_post(request):
    """Create a new blog post"""
    # Get available categories
    categories = Category.objects.all().order_by('name')
    if not categories.exists():
        # Fallback to default categories if none exist
        categories = [cat[0] for cat in Post.CATEGORY_CHOICES]
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category = request.POST.get('category')
        featured_image = request.FILES.get('featured_image')
        
        post = Post.objects.create(
            title=title,
            content=content,
            category=category,
            author=request.user,
            featured_image=featured_image
        )
        messages.success(request, 'Post created successfully!')
        return redirect('writer_dashboard')
    
    return render(request, 'blog/create_post.html', {'categories': categories})


@role_required(['Writer'])
def edit_post(request, post_id):
    """Edit an existing blog post"""
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
    # Get available categories
    categories = Category.objects.all().order_by('name')
    if not categories.exists():
        # Fallback to default categories if none exist
        categories = [cat[0] for cat in Post.CATEGORY_CHOICES]
    
    if request.method == 'POST':
        post.title = request.POST.get('title')
        post.content = request.POST.get('content')
        post.category = request.POST.get('category')
        if request.FILES.get('featured_image'):
            post.featured_image = request.FILES.get('featured_image')
        post.save()
        messages.success(request, 'Post updated successfully!')
        return redirect('writer_dashboard')
    
    context = {
        'post': post,
        'categories': categories,
    }
    return render(request, 'blog/edit_post.html', context)


@role_required(['Writer'])
def delete_post(request, post_id):
    """Soft delete own blog post"""
    if request.method == 'POST':
        post = get_object_or_404(Post.all_objects, id=post_id, author=request.user)
        if post.is_deleted:
            messages.warning(request, 'Post is already deleted.')
        else:
            post.is_deleted = True
            post.deleted_at = timezone.now()
            post.save()
            messages.success(request, 'Post deleted successfully!')
    return redirect('writer_dashboard')


@role_required(['Writer'])
def view_post_comments(request, post_id):
    """View comments on writer's own posts"""
    post = get_object_or_404(Post, id=post_id, author=request.user)
    comments = Comment.objects.filter(post=post, parent=None).order_by('created_at')
    
    context = {
        'post': post,
        'comments': comments,
    }
    return render(request, 'blog/view_comments.html', context)


@role_required(['Writer'])
def reply_comment(request, comment_id):
    """Reply to a comment on writer's post"""
    if request.method == 'POST':
        parent_comment = get_object_or_404(Comment, id=comment_id)
        # Verify the comment is on writer's post
        if parent_comment.post.author != request.user:
            messages.error(request, 'You can only reply to comments on your own posts.')
            return redirect('writer_dashboard')
        
        content = request.POST.get('content')
        Comment.objects.create(
            post=parent_comment.post,
            user=request.user,
            parent=parent_comment,
            content=content
        )
        messages.success(request, 'Reply posted successfully!')
        return redirect('view_post_comments', post_id=parent_comment.post.id)
    
    return redirect('writer_dashboard')


@role_required(['Reader', 'Writer'])
def reader_dashboard(request):
    """Reader dashboard with navigation and filters (Writers can also read blogs)"""
    posts = Post.objects.all().order_by('-created_at')
    category = request.GET.get('category')
    author_id = request.GET.get('author')
    followed_only = request.GET.get('followed') == 'true'
    search_query = request.GET.get('search', '').strip()
    
    # Apply filters
    if category:
        posts = posts.filter(category=category)
    
    if author_id:
        posts = posts.filter(author_id=author_id)
    
    if followed_only:
        followed_authors = Follow.objects.filter(follower=request.user).values_list('followed_author_id', flat=True)
        posts = posts.filter(author_id__in=followed_authors)
    
    # Enhanced search: by post title, author name, or category
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(author__username__icontains=search_query) |
            Q(author__first_name__icontains=search_query) |
            Q(author__last_name__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    # Get all categories for dropdown (from Category model, fallback to post categories)
    category_objects = Category.objects.all()
    if category_objects.exists():
        categories = [cat.name for cat in category_objects]
    else:
        categories = Post.objects.values_list('category', flat=True).distinct()
    
    # Get all authors for search
    authors = User.objects.filter(role='Writer')
    
    context = {
        'posts': posts,
        'categories': categories,
        'authors': authors,
        'selected_category': category,
        'selected_author': author_id,
        'followed_only': followed_only,
        'search_query': search_query,
    }
    return render(request, 'blog/reader_dashboard.html', context)


@role_required(['Reader', 'Writer', 'Admin'])
def post_detail(request, post_id):
    """View a single post with comments (Readers and Writers can like/comment/follow)"""
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post, parent=None).order_by('created_at')
    is_liked = False
    is_following = False
    # Allow both Readers and Writers to interact
    if request.user.role in ['Reader', 'Writer']:
        is_liked = post.is_liked_by(request.user)
        if post.author.role == 'Writer' and post.author != request.user:
            is_following = Follow.objects.filter(follower=request.user, followed_author=post.author).exists()
    
    # Get recommended posts with caching (24 hours)
    cache_key = f'recommended_posts_{post_id}'
    recommended_posts = cache.get(cache_key)
    
    if recommended_posts is None:
        recommended_posts = get_recommended_posts(post, num_recommendations=5)
        # Cache for 24 hours (86400 seconds)
        cache.set(cache_key, recommended_posts, 86400)
    
    context = {
        'post': post,
        'comments': comments,
        'is_liked': is_liked,
        'is_following': is_following,
        'recommended_posts': recommended_posts,
    }
    return render(request, 'blog/post_detail.html', context)


@role_required(['Reader', 'Writer'])
@require_POST
def toggle_like(request, post_id):
    """Toggle like on a post (Reader and Writer)"""
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    
    if not created:
        # Unlike - delete the like
        like.delete()
        liked = False
    else:
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'like_count': post.get_like_count()
    })


@role_required(['Reader', 'Writer'])
@require_POST
def add_comment(request, post_id):
    """Add a comment to a post (Reader and Writer)"""
    post = get_object_or_404(Post, id=post_id)
    content = request.POST.get('content')
    
    if content:
        Comment.objects.create(
            post=post,
            user=request.user,
            content=content
        )
        messages.success(request, 'Comment added successfully!')
    else:
        messages.error(request, 'Comment cannot be empty.')
    
    return redirect('post_detail', post_id=post_id)


@role_required(['Reader', 'Writer'])
@require_POST
def toggle_follow(request, author_id):
    """Toggle follow/unfollow an author (Reader and Writer)"""
    author = get_object_or_404(User, id=author_id, role='Writer')
    
    if author == request.user:
        return JsonResponse({'error': 'Cannot follow yourself'}, status=400)
    
    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        followed_author=author
    )
    
    if not created:
        # Unfollow - delete the follow
        follow.delete()
        following = False
    else:
        following = True
    
    return JsonResponse({
        'following': following,
        'follower_count': author.followers.count()
    })


@role_required(['Reader', 'Writer', 'Admin'])
def author_ranking(request):
    """Author ranking page based on follower count"""
    authors = User.objects.filter(role='Writer').annotate(
        follower_count=Count('followers')
    ).order_by('-follower_count', 'username')
    
    context = {
        'authors': authors,
    }
    return render(request, 'blog/author_ranking.html', context)


@login_required
def profile(request):
    """User profile dashboard with profile picture upload"""
    user = request.user
    
    if request.method == 'POST':
        # Handle profile picture upload
        if 'profile_pic' in request.FILES:
            user.profile_pic = request.FILES['profile_pic']
            user.save()
            messages.success(request, 'Profile picture updated successfully!')
            return redirect('profile')
        
        # Handle profile information update
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.middle_name = request.POST.get('middle_name', user.middle_name)
        user.email = request.POST.get('email', user.email)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.gender = request.POST.get('gender', user.gender)
        user.bio = request.POST.get('bio', user.bio)
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    context = {
        'user': user,
    }
    return render(request, 'blog/profile.html', context)


@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    return render(request, 'blog/change_password.html', {'form': form})


@login_required
def request_writer(request):
    """Reader can request to become Writer"""
    if request.user.role != 'Reader':
        messages.error(request, 'Only Readers can request to become Writers.')
        return redirect('profile')
    
    if request.method == 'POST':
        form = WriterRequestForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.writer_request = True
            user.save()
            messages.success(request, 'Your request to become a Writer has been submitted. Admin will review it.')
            return redirect('profile')
    else:
        form = WriterRequestForm(instance=request.user)
    
    return render(request, 'blog/request_writer.html', {'form': form})


@role_required(['Admin'])
def approve_writer(request, user_id):
    """Admin approves a Writer registration"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id, role='Writer')
        user.is_approved = True
        user.save()
        messages.success(request, f'Writer {user.username} has been approved.')
    return redirect('admin_dashboard')


@role_required(['Admin'])
def approve_writer_request(request, user_id):
    """Admin approves a Reader's request to become Writer"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id, role='Reader', writer_request=True)
        user.role = 'Writer'
        user.writer_request = False
        user.writer_request_message = None
        user.is_approved = True
        user.save()
        messages.success(request, f'{user.username} has been upgraded to Writer.')
    return redirect('admin_dashboard')


@role_required(['Admin'])
def reject_writer_request(request, user_id):
    """Admin rejects a Reader's request to become Writer"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id, role='Reader', writer_request=True)
        user.writer_request = False
        user.writer_request_message = None
        user.save()
        messages.success(request, f'Writer request from {user.username} has been rejected.')
    return redirect('admin_dashboard')


@role_required(['Admin'])
def create_admin(request):
    """Admin creates a new admin account"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if not all([first_name, last_name, email, password, password_confirm]):
            messages.error(request, 'All fields are required.')
            return redirect('admin_dashboard')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return redirect('admin_dashboard')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return redirect('admin_dashboard')
        
        # Generate unique username
        username = generate_unique_username(first_name, last_name)
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='Admin',
            is_approved=True,
            is_staff=True,
            is_superuser=True
        )
        messages.success(request, f'Admin account created successfully! Username: {user.username}')
        return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')


@role_required(['Admin'])
def add_category(request):
    """Admin adds a new category"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, 'Category name is required.')
            return redirect('admin_dashboard')
        
        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, 'A category with this name already exists.')
            return redirect('admin_dashboard')
        
        category = Category.objects.create(
            name=name,
            description=description if description else None
        )
        messages.success(request, f'Category "{category.name}" added successfully!')
        return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')


@role_required(['Admin'])
def delete_category(request, category_id):
    """Admin soft deletes a category"""
    if request.method == 'POST':
        category = get_object_or_404(Category.all_objects, id=category_id)
        if category.is_deleted:
            messages.warning(request, f'Category "{category.name}" is already deleted.')
        else:
            category_name = category.name
            category.is_deleted = True
            category.deleted_at = timezone.now()
            category.save()
            messages.success(request, f'Category "{category_name}" deleted successfully!')
    return redirect('admin_dashboard')


@role_required(['Admin'])
def restore_user(request, user_id):
    """Admin restores a deleted user"""
    if request.method == 'POST':
        user = get_object_or_404(User.all_objects, id=user_id, is_deleted=True)
        user.is_deleted = False
        user.deleted_at = None
        user.save()
        messages.success(request, f'User {user.username} has been restored.')
    return redirect('admin_dashboard')


@role_required(['Admin'])
def restore_post(request, post_id):
    """Admin restores a deleted post"""
    if request.method == 'POST':
        post = get_object_or_404(Post.all_objects, id=post_id, is_deleted=True)
        post.is_deleted = False
        post.deleted_at = None
        post.save()
        messages.success(request, f'Post "{post.title}" has been restored.')
    return redirect('admin_dashboard')


@role_required(['Admin'])
def restore_category(request, category_id):
    """Admin restores a deleted category"""
    if request.method == 'POST':
        category = get_object_or_404(Category.all_objects, id=category_id, is_deleted=True)
        category.is_deleted = False
        category.deleted_at = None
        category.save()
        messages.success(request, f'Category "{category.name}" has been restored.')
    return redirect('admin_dashboard')


@role_required(['Writer'])
def request_restore_post(request, post_id):
    """Writer requests admin to restore a deleted post"""
    if request.method == 'POST':
        post = get_object_or_404(Post.all_objects, id=post_id, author=request.user, is_deleted=True)
        
        # Check if there's already a pending request for this post
        existing_request = RestoreRequest.objects.filter(
            post=post, 
            status='Pending'
        ).first()
        
        if existing_request:
            messages.warning(request, 'You already have a pending restore request for this post.')
        else:
            message = request.POST.get('message', '').strip()
            RestoreRequest.objects.create(
                post=post,
                writer=request.user,
                message=message if message else None,
                status='Pending'
            )
            messages.success(request, 'Restore request submitted successfully! Admin will review it soon.')
    
    return redirect('writer_dashboard')


@role_required(['Admin'])
def approve_restore_request(request, request_id):
    """Admin approves a restore request and restores the post"""
    if request.method == 'POST':
        restore_request = get_object_or_404(RestoreRequest, id=request_id, status='Pending')
        post = restore_request.post
        
        # Restore the post
        post.is_deleted = False
        post.deleted_at = None
        post.save()
        
        # Update restore request
        restore_request.status = 'Approved'
        restore_request.reviewed_at = timezone.now()
        restore_request.reviewed_by = request.user
        restore_request.save()
        
        messages.success(request, f'Post "{post.title}" has been restored successfully.')
    return redirect('admin_dashboard')


@role_required(['Admin'])
def reject_restore_request(request, request_id):
    """Admin rejects a restore request"""
    if request.method == 'POST':
        restore_request = get_object_or_404(RestoreRequest, id=request_id, status='Pending')
        post_title = restore_request.post.title
        
        # Update restore request
        restore_request.status = 'Rejected'
        restore_request.reviewed_at = timezone.now()
        restore_request.reviewed_by = request.user
        restore_request.save()
        
        messages.success(request, f'Restore request for "{post_title}" has been rejected.')
    return redirect('admin_dashboard')


@role_required(['Admin'])
def admin_dashboard(request):
    """Admin dashboard with user and post management"""
    users = User.objects.exclude(id=request.user.id).order_by('-date_joined')
    posts = Post.objects.all().order_by('-created_at')
    
    # Pending Writer approvals (writers need approval now)
    pending_writers = User.objects.filter(role='Writer', is_approved=False).order_by('date_joined')
    
    # Pending Writer requests (readers requesting to become writers)
    pending_writer_requests = User.objects.filter(role='Reader', writer_request=True).order_by('date_joined')
    
    # Pending restore requests (with error handling for missing table)
    try:
        pending_restore_requests = RestoreRequest.objects.filter(status='Pending').order_by('-created_at')
    except Exception as e:
        # Table doesn't exist yet - migrations not applied
        # This will be resolved once migrations are applied
        pending_restore_requests = RestoreRequest.objects.none()
        if 'no such table' in str(e).lower() or 'does not exist' in str(e).lower():
            messages.warning(request, 'RestoreRequest table not found. Please run: python manage.py migrate')
    
    # Get all categories
    categories = Category.objects.all().order_by('name')
    
    # Get deleted items for restore section
    deleted_users = User.all_objects.filter(is_deleted=True).order_by('-deleted_at')
    deleted_posts = Post.all_objects.filter(is_deleted=True).order_by('-deleted_at')
    deleted_categories = Category.all_objects.filter(is_deleted=True).order_by('-deleted_at')
    
    context = {
        'users': users,
        'posts': posts,
        'pending_writers': pending_writers,
        'pending_writer_requests': pending_writer_requests,
        'pending_restore_requests': pending_restore_requests,
        'categories': categories,
        'deleted_users': deleted_users,
        'deleted_posts': deleted_posts,
        'deleted_categories': deleted_categories,
    }
    return render(request, 'blog/admin_dashboard.html', context)

