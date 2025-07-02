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
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.dept_admin_logout, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('ticket/<int:ticket_id>/', views.view_ticket, name='view_ticket'),
    path('manage-sla/', views.manage_sla, name='manage_sla'),
    path('update-complaint/<int:complaint_id>/', views.update_complaint, name='update_complaint'),
    path('export-complaints/', views.export_complaints, name='export_complaints'),
    path('sla-dashboard/', views.dept_sla_dashboard, name='sla_dashboard'),
    path('manage-sla-config/', views.manage_sla_config, name='manage_sla_config'),
    path('sla-breach-report/', views.sla_breach_report, name='sla_breach_report'),
    path('create-student/', views.create_student, name='create_student'),
    path('escalate-ticket/<int:ticket_id>/', views.escalate_ticket, name='escalate_ticket'),
    path('view-tickets/<str:priority>/', views.view_tickets, name='view_tickets'),
    path('escalate-priority/<str:priority>/', views.escalate_priority, name='escalate_priority'),
    path('bulk-create-students/', views.bulk_create_students, name='bulk_create_students'),
    path('download-template/', views.download_template, name='download_template'),
    path('escalated-tickets/', views.general_escalated_tickets, name='escalated_tickets'),
    path('handle-escalated-ticket/<int:ticket_id>/', views.handle_escalated_ticket, name='handle_escalated_ticket'),
    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),

    # Department admin sites with unique namespaces
    path('finance/', finance_admin_site.urls, name='finance_admin'),
    path('hostel/', hostel_admin_site.urls, name='hostel_admin'),
    path('mess/', mess_admin_site.urls, name='mess_admin'),
    path('academics/', academics_admin_site.urls, name='academics_admin'),
    path('others/', others_admin_site.urls, name='others_admin'),
    path('gatepass/', gatepass_admin_site.urls, name='gatepass_admin'),
]
