from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import Complaint, Department, StudentProfile, DepartmentProfile, AuditLog

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'

class DepartmentProfileInline(admin.StackedInline):
    model = DepartmentProfile
    can_delete = False
    verbose_name_plural = 'Department Profile'

class CustomUserAdmin(DefaultUserAdmin):
    inlines = (StudentProfileInline, DepartmentProfileInline)

# Unregister and re-register User with the custom inline admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register other models
admin.site.register(Department)
admin.site.register(Complaint)
admin.site.register(AuditLog)
admin.site.register(StudentProfile)
admin.site.register(DepartmentProfile)
