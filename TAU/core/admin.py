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
    inlines = [DepartmentProfileInline, StudentProfileInline]
    list_display = ('username', 'email', 'is_staff', 'is_superuser')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Complaint)
admin.site.register(Department)
admin.site.register(AuditLog)
