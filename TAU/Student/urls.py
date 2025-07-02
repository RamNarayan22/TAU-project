from django.urls import path
from . import views
from django.http import Http404

app_name = 'student'

def temp_404(request):
    raise Http404("Registration is disabled")

urlpatterns = [
    # Root URL should check user type and redirect accordingly
    path('', views.student_root, name='root'),
    
    # Authentication URLs
    path('login/', views.lp, name='loginn'),
    path('logout/', views.logout_view, name='logout'),
    path('accounts/login/', views.lp),
    path('change-password/', views.change_password, name='change_password'),
    path('register/', temp_404, name='register'),  # Temporary 404 handler
    path('complete-registration/', views.complete_registration, name='complete_registration'),
    
    # Student dashboard URLs
    path('newticket/', views.nt, name='nt'), # for student dashboard
    path('landingpage/', views.landingpage, name='landingpage'), # for student dashboard
    path('sla-dashboard/', views.sla_dashboard, name='sla_dashboard'),
    path('tickets/', views.view_tickets, name='view_tickets'),
    path('ticket/<int:ticket_id>/details/', views.ticket_details, name='ticket_details'),
]