"""
URL configuration for TAU project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from core.admin import (
    finance_admin_site,
    hostel_admin_site,
    mess_admin_site,
    academics_admin_site,
    others_admin_site,
    gatepass_admin_site,
)

def root_redirect(request):
    """
    Root URL handler that always directs to student login by default
    """
    # Always redirect to student login page for the root URL
    return redirect('student:loginn')

urlpatterns = [
    # Root URL always redirects to student login
    path('', root_redirect, name='root'),
    
    # Admin URLs - only accessible through direct department admin login URL
    path('admin/', admin.site.urls),
    path('student/', include('Student.urls')),        # all student URLs prefixed by /student/
    path('department/', include('dept_admin.urls')),  # all admin URLs prefixed by /department/
    
    # Department-specific admin sites with unique namespaces
    path('finance-admin/', finance_admin_site.urls, name='finance_admin_site'),
    path('hostel-admin/', hostel_admin_site.urls, name='hostel_admin_site'),
    path('mess-admin/', mess_admin_site.urls, name='mess_admin_site'),
    path('academics-admin/', academics_admin_site.urls, name='academics_admin_site'),
    path('others-admin/', others_admin_site.urls, name='others_admin_site'),
    path('gatepass-admin/', gatepass_admin_site.urls, name='gatepass_admin_site'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
