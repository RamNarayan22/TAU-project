from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from django.contrib.auth import logout

def student_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('student:loginn')
        
        try:
            from core.models import Profile
            profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'is_admin': request.user.is_staff})
            # Student: not admin, not staff, not superuser
            if profile.is_admin or request.user.is_staff or request.user.is_superuser:
                messages.error(request, 'Access denied. This page is for students only.')
                logout(request)
                request.session.flush()
                return redirect('choose_portal')
        except Exception:
            messages.error(request, 'Invalid user profile.')
            logout(request)
            request.session.flush()
            return redirect('choose_portal')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def dept_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dept_admin:login')
        
        try:
            # Check if user is a department admin using is_admin flag
            if not (request.user.is_superuser or request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.is_admin)):
                messages.error(request, 'Access denied. This page is for department administrators only.')
                logout(request)
                request.session.flush()
                return redirect('choose_portal')
        except Exception:
            messages.error(request, 'Invalid user profile.')
            logout(request)
            request.session.flush()
            return redirect('choose_portal')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        
        try:
            if request.user.profile.role != 'superuser':
                messages.error(request, 'Access denied. This page is for superusers only.')
                if request.user.profile.role == 'student':
                    return redirect('student:landingpage')
                elif request.user.profile.role == 'dept_admin':
                    return redirect('dept_admin:dashboard')
                return redirect('core:login')
        except:
            messages.error(request, 'Invalid user profile.')
            return redirect('core:login')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view 