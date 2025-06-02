from django.contrib import admin
from core.models import Complaint

class DepartmentComplaintAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'get_student', 'description', 'status', 'created_at')
    list_filter = ('status',)

    def get_student(self, obj):
        return obj.user.username if obj.user else '-'
    get_student.short_description = 'Student'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(self.admin_site, 'department_name') and self.admin_site.department_name:
            return qs.filter(department__name=self.admin_site.department_name)
        return qs
