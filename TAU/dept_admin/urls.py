
from django.urls import path
from .views import login_view, dashboard_view, export_csv, update_complaint



from django.contrib import admin


#  custom admin site instances 
from Student.admin import (
    finance_admin_site,
    hostel_admin_site,
    mess_admin_site,
    academics_admin_site,
    others_admin_site,
    gatepass_admin_site,
)

urlpatterns = [
    
    

    path('finance/', finance_admin_site.urls),
    path('hostel/', hostel_admin_site.urls),
    path('mess/', mess_admin_site.urls),
    path('academics/', academics_admin_site.urls),
    path('others/', others_admin_site.urls),
    path('gatepass/', gatepass_admin_site.urls),
    path('', login_view, name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('dashboard/export-csv/', export_csv, name='export_csv'),
    path('update/<int:complaint_id>/', update_complaint, name='update_complaint'),

    
]
