from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html

# Base custom AdminSite with department name attribute
class BaseDepartmentAdminSite(AdminSite):
    department_name = None

    def has_permission(self, request):
        # Only staff users can access
        return (
            request.user.is_active and 
            request.user.is_staff and
            hasattr(request.user, 'profile') and
            request.user.profile.department and
            request.user.profile.department.name == self.department_name
        )

    def each_context(self, request):
        context = super().each_context(request)
        context['department_name'] = self.department_name
        return context


# Custom admin sites for each department
class FinanceAdminSite(BaseDepartmentAdminSite):
    department_name = 'Finance'
    site_header = 'Finance Department Admin'


class HostelAdminSite(BaseDepartmentAdminSite):
    department_name = 'Hostel'
    site_header = 'Hostel Department Admin'


class MessAdminSite(BaseDepartmentAdminSite):
    department_name = 'Mess'
    site_header = 'Mess Department Admin'


class AcademicsAdminSite(BaseDepartmentAdminSite):
    department_name = 'Academics'
    site_header = 'Academics Department Admin'


class OthersAdminSite(BaseDepartmentAdminSite):
    department_name = 'Others'
    site_header = 'Others Department Admin'


class GatePassAdminSite(BaseDepartmentAdminSite):
    department_name = 'Gate Pass'
    site_header = 'Gate Pass Department Admin'
