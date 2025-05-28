from django.urls import path
from .views import login_view, dashboard, update_complaint, export_csv


from .admin_sites import (
    finance_admin_site,
    hostel_admin_site,
    mess_admin_site,
    academics_admin_site,
    others_admin_site,
    gatepass_admin_site,
)

urlpatterns = [
    path('', login_view, name='login'),
    path('dashboard/',dashboard, name='department_dashboard'),
    path('update/<int:complaint_id>/', update_complaint, name='update_complaint'),
    path('dashboard/export-csv/', export_csv, name='export_csv'),

    # Department admin sites
    path('finance/', finance_admin_site.urls),
    path('hostel/', hostel_admin_site.urls),
    path('mess/', mess_admin_site.urls),
    path('academics/', academics_admin_site.urls),
    path('others/', others_admin_site.urls),
    path('gatepass/', gatepass_admin_site.urls),
]
