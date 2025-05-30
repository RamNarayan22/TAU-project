from django.contrib.admin import AdminSite
from core.models import Complaint
from dept_admin.admin import DepartmentComplaintAdmin

class BaseDepartmentAdminSite(AdminSite):
    department_name = None

    def has_permission(self, request):
        return (
            request.user.is_active
            and request.user.is_staff
            and hasattr(request.user, 'profile')
            and request.user.profile.department == self.department_name
        )

    def each_context(self, request):
        context = super().each_context(request)
        context['department_name'] = self.department_name
        return context

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

finance_admin_site = FinanceAdminSite(name='finance_admin')
hostel_admin_site = HostelAdminSite(name='hostel_admin')
mess_admin_site = MessAdminSite(name='mess_admin')
academics_admin_site = AcademicsAdminSite(name='academics_admin')
others_admin_site = OthersAdminSite(name='others_admin')
gatepass_admin_site = GatePassAdminSite(name='gatepass_admin')

def register_department_complaints():
    for site in [
        finance_admin_site,
        hostel_admin_site,
        mess_admin_site,
        academics_admin_site,
        others_admin_site,
        gatepass_admin_site,
    ]:
        site.register(Complaint, DepartmentComplaintAdmin)
