from django.contrib import admin
from django.urls import path
from dept_admin.admin import (
    finance_admin_site,
    hostel_admin_site,
    mess_admin_site,
    academics_admin_site,
    others_admin_site,
    gatepass_admin_site,
)
from dept_admin.views import login_view

urlpatterns = [
    path('admin/finance/', finance_admin_site.urls),
    path('admin/hostel/', hostel_admin_site.urls),
    path('admin/mess/', mess_admin_site.urls),
    path('admin/academics/', academics_admin_site.urls),
    path('admin/others/', others_admin_site.urls),
    path('admin/gatepass/', gatepass_admin_site.urls),

    path('login/', login_view, name='login'),
]
