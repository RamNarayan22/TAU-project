from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.db import transaction

from .models import Complaint, Department, Profile, AuditLog

class DepartmentFacultyCreationForm(UserCreationForm):
    department = forms.ModelChoiceField(queryset=Department.objects.all())
    is_admin = forms.BooleanField(required=False, initial=True,
                                help_text='Designates whether the user can access department admin panel')

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name')

    def save(self, commit=True):
        with transaction.atomic():
            user = super().save(commit=False)
            user.is_staff = True
            if commit:
                user.save()
                # Create or update profile
                profile, created = Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        'department': self.cleaned_data['department'],
                        'is_admin': self.cleaned_data['is_admin'],
                        'must_change_password': True
                    }
                )
                if not created:
                    profile.department = self.cleaned_data['department']
                    profile.is_admin = self.cleaned_data['is_admin']
                    profile.must_change_password = True
                    profile.save()
            return user

# Inline admin for Profile
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'

# Custom User Admin with Profile inline
class CustomUserAdmin(DefaultUserAdmin):
    inlines = (ProfileInline,)
    add_form = DepartmentFacultyCreationForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'department', 'is_admin'),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        if not obj and request.user.is_superuser:  # Only for adding new users
            kwargs['form'] = self.add_form
        return super().get_form(request, obj, **kwargs)

# Unregister and re-register User with the custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Base Department Admin Site
class BaseDepartmentAdminSite(AdminSite):
    department_name = None

    def has_permission(self, request):
        return (
            request.user.is_active and
            request.user.is_staff and
            hasattr(request.user, 'profile') and
            request.user.profile.department and
            request.user.profile.department.name == self.department_name and
            request.user.profile.is_admin
        )

    def each_context(self, request):
        context = super().each_context(request)
        context['department_name'] = self.department_name
        return context

# Department-specific Admin Sites
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

# Department Complaint Admin
class DepartmentComplaintAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'get_student', 'description', 'status', 'created_at')
    list_filter = ('status',)
    readonly_fields = ('ticket_id',)

    def get_student(self, obj):
        return obj.user.username if obj.user else '-'
    get_student.short_description = 'Student'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(self.admin_site, 'department_name') and self.admin_site.department_name:
            return qs.filter(department__name=self.admin_site.department_name)
        return qs

# Main Admin Site Complaint Admin
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'get_student', 'department', 'status', 'created_at')
    list_filter = ('department', 'status', 'created_at')
    search_fields = ('ticket_id', 'description', 'user__username')
    readonly_fields = ('ticket_id', 'created_at')

    def get_student(self, obj):
        return obj.user.username if obj.user else 'Anonymous'
    get_student.short_description = 'Student'

# Instantiate department admin sites
finance_admin_site = FinanceAdminSite(name='finance_admin')
hostel_admin_site = HostelAdminSite(name='hostel_admin')
mess_admin_site = MessAdminSite(name='mess_admin')
academics_admin_site = AcademicsAdminSite(name='academics_admin')
others_admin_site = OthersAdminSite(name='others_admin')
gatepass_admin_site = GatePassAdminSite(name='gatepass_admin')

# Register models with department admin sites
for site in [
    finance_admin_site,
    hostel_admin_site,
    mess_admin_site,
    academics_admin_site,
    others_admin_site,
    gatepass_admin_site,
]:
    site.register(Complaint, DepartmentComplaintAdmin)

# Register models with main admin site
admin.site.register(Department)
admin.site.register(Complaint, ComplaintAdmin)

class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'performed_by', 'action', 'timestamp')
    list_filter = ('timestamp', 'performed_by')
    search_fields = ('complaint__ticket_id', 'action', 'performed_by__username')
    readonly_fields = ('complaint', 'performed_by', 'action', 'timestamp')

admin.site.register(AuditLog, AuditLogAdmin)
