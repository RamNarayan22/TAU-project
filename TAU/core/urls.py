from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # ... existing URLs ...
    path('sla-dashboard/', views.global_sla_dashboard, name='global_sla_dashboard'),
    path('sla-config/', views.global_sla_config, name='global_sla_config'),
    path('sla-report/', views.global_sla_report, name='global_sla_report'),
] 