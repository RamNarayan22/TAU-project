from django.contrib import admin
from Student.models import Ticket

class DepartmentComplaintAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'get_student', 'subject', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'department')
    search_fields = ('ticket_id', 'subject', 'description', 'student__username', 'student__email')
    readonly_fields = ('ticket_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def get_student(self, obj):
        return obj.student.username if obj.student else '-'
    get_student.short_description = 'Student'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(self.admin_site, 'department_name') and self.admin_site.department_name:
            return qs.filter(department__name=self.admin_site.department_name)
        return qs

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'student', 'department', 'subject', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'department')
    search_fields = ('ticket_id', 'subject', 'description', 'student__username', 'student__email')
    readonly_fields = ('ticket_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
