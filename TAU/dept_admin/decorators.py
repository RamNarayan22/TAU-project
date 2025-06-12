from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from django.contrib.auth import logout

def is_dept_admin(user):
    """
    Check if the user is a department admin
    """
    return (user.is_authenticated and 
            (user.is_superuser or user.is_staff or 
             (hasattr(user, 'profile') and user.profile.is_admin)))

def dept_admin_required(view_func):
    """
    Decorator for views that checks that the user is a department admin,
    redirecting to the login page if necessary.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('dept_admin:login')
        
        if not is_dept_admin(request.user):
            messages.error(request, 'Access denied. This page is for department admins only.')
            logout(request)
            request.session.flush()
            return redirect('choose_portal')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view 