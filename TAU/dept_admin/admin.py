from django.contrib import admin
from core.models import Complaint

class DepartmentComplaintAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'student', 'description', 'status', 'created_at')
    list_filter = ('status',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(self.admin_site, 'department_name') and self.admin_site.department_name:
            return qs.filter(department__name=self.admin_site.department_name)
        return qs
