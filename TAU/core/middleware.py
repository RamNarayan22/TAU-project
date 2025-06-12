from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout
from django.contrib import messages

class DisableHTTPSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Preserve original request properties
        original_is_secure = request.is_secure
        original_scheme = request.META.get('wsgi.url_scheme', 'http')

        # Force HTTP for development
        request.is_secure = lambda: False
        request._is_secure = False
        request.META['wsgi.url_scheme'] = 'http'
        
        try:
            response = self.get_response(request)
            return response
        finally:
            # Restore original properties
            request.is_secure = original_is_secure
            request.META['wsgi.url_scheme'] = original_scheme

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_staff:
            profile = getattr(request.user, 'profile', None)
            
            # Check if user has a valid profile
            if not profile:
                messages.error(request, 'Invalid user profile. Please contact support.')
                logout(request)
                return redirect('student:loginn')
            
            # Check if password change is required
            if profile.must_change_password:
                # Allow access to logout and password change pages
                allowed_paths = [
                    reverse('student:change_password'),
                    reverse('student:logout'),
                    reverse('dept_admin:logout'),
                ]
                if request.path not in allowed_paths:
                    messages.info(request, 'Please change your password to continue.')
                    return redirect('student:change_password')
        
        response = self.get_response(request)
        return response

