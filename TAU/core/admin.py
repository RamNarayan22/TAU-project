from django.contrib import admin
from .models import Complaint, Department, DepartmentProfile, AuditLog

admin.site.register(Complaint)
admin.site.register(Department)
admin.site.register(DepartmentProfile)
admin.site.register(AuditLog)