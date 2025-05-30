from django.urls import path
from . import views
from .admin_sites import (
    finance_admin_site,
    hostel_admin_site,
    mess_admin_site,
    academics_admin_site,
    others_admin_site,
    gatepass_admin_site,
)

app_name = 'dept_admin'

urlpatterns = [
    path('login/', views.dept_admin_login, name='login'),
    path('logout/', views.dept_admin_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('complaint/<int:complaint_id>/update/', views.update_complaint, name='update_complaint'),
    path('export/', views.export_complaints, name='export_complaints'),

    # Department admin sites with unique namespaces
    path('finance/', finance_admin_site.urls, name='finance_admin'),
    path('hostel/', hostel_admin_site.urls, name='hostel_admin'),
    path('mess/', mess_admin_site.urls, name='mess_admin'),
    path('academics/', academics_admin_site.urls, name='academics_admin'),
    path('others/', others_admin_site.urls, name='others_admin'),
    path('gatepass/', gatepass_admin_site.urls, name='gatepass_admin'),
]
