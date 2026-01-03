from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles):
    """Decorator to restrict access based on user role"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please login to access this page.')
                return redirect('login')
            
            if request.user.role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                # Redirect based on user role
                if request.user.role == 'Admin':
                    return redirect('admin_dashboard')
                elif request.user.role == 'Writer':
                    return redirect('writer_dashboard')
                else:
                    return redirect('reader_dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


