from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from .models import Complaint


# Custom ModelAdmin filtering complaints by department of the admin site
class DepartmentComplaintAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'user', 'description', 'status', 'created_at')
    list_filter = ('status',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(self.admin_site, 'department_name') and self.admin_site.department_name:
            return qs.filter(department=self.admin_site.department_name)
        return qs


# Base custom AdminSite with department name attribute
class BaseDepartmentAdminSite(AdminSite):
    department_name = None

    def has_permission(self, request):
        # Only staff users can access
        return request.user.is_active and request.user.is_staff

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


# Instantiate custom admin sites
finance_admin_site = FinanceAdminSite(name='finance_admin')
hostel_admin_site = HostelAdminSite(name='hostel_admin')
mess_admin_site = MessAdminSite(name='mess_admin')
academics_admin_site = AcademicsAdminSite(name='academics_admin')
others_admin_site = OthersAdminSite(name='others_admin')
gatepass_admin_site = GatePassAdminSite(name='gatepass_admin')


# Register Complaint model with each custom admin site
for site in [
    finance_admin_site,
    hostel_admin_site,
    mess_admin_site,
    academics_admin_site,
    others_admin_site,
    gatepass_admin_site,
]:
    site.register(Complaint, DepartmentComplaintAdmin)


# Default admin for the main Django admin site
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'department', 'short_description', 'attachment_link', 'status')
    readonly_fields = ('ticket_id', 'attachment_link')

    def short_description(self, obj):
        if len(obj.description) > 50:
            return obj.description[:50] + '...'
        return obj.description
    short_description.short_description = 'Description'

    def attachment_link(self, obj):
        if obj.attachment:
            return format_html('<a href="{}" target="_blank">View</a>', obj.attachment.url)
        return "No attachment"
    attachment_link.short_description = 'Attachment'


# Register with the default admin site
admin.site.register(Complaint, ComplaintAdmin)
