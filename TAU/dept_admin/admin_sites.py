from django.contrib.admin import AdminSite
from Student.models import Ticket
from dept_admin.admin import DepartmentComplaintAdmin

class BaseDepartmentAdminSite(AdminSite):
    department_name = None

    def has_permission(self, request):
        """
        Return True if the given HttpRequest has permission to view
        *any* page in the admin site.
        """
        return (
            request.user.is_active
            and request.user.is_staff
            and hasattr(request.user, 'profile')
            and request.user.profile.department.name == self.department_name
        )

    def each_context(self, request):
        context = super().each_context(request)
        context['department_name'] = self.department_name
        return context

class FinanceAdminSite(BaseDepartmentAdminSite):
    department_name = 'Finance'
    site_header = 'Finance Department Admin'
    site_title = 'Finance Department Portal'
    index_title = 'Finance Department Management'

class HostelAdminSite(BaseDepartmentAdminSite):
    department_name = 'Hostel'
    site_header = 'Hostel Department Admin'
    site_title = 'Hostel Department Portal'
    index_title = 'Hostel Department Management'

class MessAdminSite(BaseDepartmentAdminSite):
    department_name = 'Mess'
    site_header = 'Mess Department Admin'
    site_title = 'Mess Department Portal'
    index_title = 'Mess Department Management'

class AcademicsAdminSite(BaseDepartmentAdminSite):
    department_name = 'Academics'
    site_header = 'Academics Department Admin'
    site_title = 'Academics Department Portal'
    index_title = 'Academics Department Management'

class OthersAdminSite(BaseDepartmentAdminSite):
    department_name = 'Others'
    site_header = 'Others Department Admin'
    site_title = 'Others Department Portal'
    index_title = 'Others Department Management'

class GatePassAdminSite(BaseDepartmentAdminSite):
    department_name = 'Gate Pass'
    site_header = 'Gate Pass Department Admin'
    site_title = 'Gate Pass Department Portal'
    index_title = 'Gate Pass Department Management'

# Create instances of each department's admin site
finance_admin_site = FinanceAdminSite(name='finance_admin')
hostel_admin_site = HostelAdminSite(name='hostel_admin')
mess_admin_site = MessAdminSite(name='mess_admin')
academics_admin_site = AcademicsAdminSite(name='academics_admin')
others_admin_site = OthersAdminSite(name='others_admin')
gatepass_admin_site = GatePassAdminSite(name='gatepass_admin')

def register_department_complaints():
    """Register the Ticket model with each department's admin site"""
    for site in [
        finance_admin_site,
        hostel_admin_site,
        mess_admin_site,
        academics_admin_site,
        others_admin_site,
        gatepass_admin_site,
    ]:
        site.register(Ticket, DepartmentComplaintAdmin)
