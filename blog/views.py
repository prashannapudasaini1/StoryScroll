from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import User, Post, Comment, Like, Follow
from .decorators import role_required
from .forms import RegistrationForm, CustomPasswordChangeForm, WriterRequestForm
from .utils import generate_unique_username


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
            # Check if Reader is approved
            if user.role == 'Reader' and not user.is_approved:
                messages.warning(request, 'Your account is pending admin approval. Please wait for approval.')
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
    """Registration for Writer (auto-approved)"""
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
            user.is_approved = True  # Writers are auto-approved
            user.save()
            messages.success(request, f'Writer account created successfully! Your username is: {user.username}. You can now login.')
            return redirect('login')
    else:
        form = RegistrationForm()
    
    return render(request, 'blog/register.html', {
        'form': form,
        'user_type': 'Writer',
        'title': 'Register as Writer'
    })


def register_reader(request):
    """Registration for Reader (requires admin approval)"""
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
            user.is_approved = False  # Readers need admin approval
            user.save()
            messages.success(request, f'Reader account created! Your username is: {user.username}. Please wait for admin approval before you can login.')
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
def admin_dashboard(request):
    """Admin dashboard with user and post management"""
    users = User.objects.exclude(id=request.user.id).order_by('-date_joined')
    posts = Post.objects.all().order_by('-created_at')
    
    # Pending Reader approvals
    pending_readers = User.objects.filter(role='Reader', is_approved=False).order_by('date_joined')
    
    # Pending Writer requests
    pending_writer_requests = User.objects.filter(role='Reader', writer_request=True).order_by('date_joined')
    
    context = {
        'users': users,
        'posts': posts,
        'pending_readers': pending_readers,
        'pending_writer_requests': pending_writer_requests,
    }
    return render(request, 'blog/admin_dashboard.html', context)


@role_required(['Admin'])
def delete_user(request, user_id):
    """Delete a user account (Admin only)"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.role == 'Admin' and user != request.user:
            messages.error(request, 'Cannot delete another admin account.')
        else:
            user.delete()
            messages.success(request, f'User {user.username} has been deleted.')
    return redirect('admin_dashboard')


@role_required(['Admin'])
def delete_post_admin(request, post_id):
    """Delete any post (Admin only)"""
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        post.delete()
        messages.success(request, 'Post has been deleted.')
    return redirect('admin_dashboard')


@role_required(['Writer'])
def writer_dashboard(request):
    """Writer dashboard with post management"""
    posts = Post.objects.filter(author=request.user).order_by('-created_at')
    
    context = {
        'posts': posts,
    }
    return render(request, 'blog/writer_dashboard.html', context)


@role_required(['Writer'])
def create_post(request):
    """Create a new blog post"""
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
    
    return render(request, 'blog/create_post.html')


@role_required(['Writer'])
def edit_post(request, post_id):
    """Edit an existing blog post"""
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
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
    }
    return render(request, 'blog/edit_post.html', context)


@role_required(['Writer'])
def delete_post(request, post_id):
    """Delete own blog post"""
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id, author=request.user)
        post.delete()
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


@role_required(['Reader'])
def reader_dashboard(request):
    """Reader dashboard with navigation and filters"""
    posts = Post.objects.all().order_by('-created_at')
    category = request.GET.get('category')
    author_id = request.GET.get('author')
    followed_only = request.GET.get('followed') == 'true'
    search_author = request.GET.get('search_author')
    
    # Apply filters
    if category:
        posts = posts.filter(category=category)
    
    if author_id:
        posts = posts.filter(author_id=author_id)
    
    if followed_only:
        followed_authors = Follow.objects.filter(follower=request.user).values_list('followed_author_id', flat=True)
        posts = posts.filter(author_id__in=followed_authors)
    
    if search_author:
        posts = posts.filter(author__username__icontains=search_author)
    
    # Get all categories for dropdown
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
    }
    return render(request, 'blog/reader_dashboard.html', context)


@role_required(['Reader', 'Writer', 'Admin'])
def post_detail(request, post_id):
    """View a single post with comments (all roles can view, but only Readers can like/comment)"""
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post, parent=None).order_by('created_at')
    is_liked = False
    is_following = False
    if request.user.role == 'Reader':
        is_liked = post.is_liked_by(request.user)
        if post.author.role == 'Writer':
            is_following = Follow.objects.filter(follower=request.user, followed_author=post.author).exists()
    
    context = {
        'post': post,
        'comments': comments,
        'is_liked': is_liked,
        'is_following': is_following,
    }
    return render(request, 'blog/post_detail.html', context)


@role_required(['Reader'])
@require_POST
def toggle_like(request, post_id):
    """Toggle like on a post (Reader only)"""
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


@role_required(['Reader'])
@require_POST
def add_comment(request, post_id):
    """Add a comment to a post (Reader only)"""
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


@role_required(['Reader'])
@require_POST
def toggle_follow(request, author_id):
    """Toggle follow/unfollow an author (Reader only)"""
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
    """User profile dashboard"""
    user = request.user
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
def approve_reader(request, user_id):
    """Admin approves a Reader registration"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id, role='Reader')
        user.is_approved = True
        user.save()
        messages.success(request, f'Reader {user.username} has been approved.')
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

