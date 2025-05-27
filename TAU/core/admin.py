from django.contrib import admin
from django.contrib.auth.models import User
from core.models import Department, Complaint, AuditLog, DepartmentProfile, StudentProfile

class DepartmentProfileInline(admin.StackedInline):
    model = DepartmentProfile
    can_delete = False
    verbose_name_plural = "Department Profile"

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = "Student Profile"

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_superuser')

    def get_inline_instances(self, request, obj=None):
        inlines = []
        if obj:
            if obj.is_staff:
                inlines.append(DepartmentProfileInline(self.model, self.admin_site))
            else:
                inlines.append(StudentProfileInline(self.model, self.admin_site))
        return inlines

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Complaint)
admin.site.register(Department)
admin.site.register(AuditLog)
