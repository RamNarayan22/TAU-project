from django.apps import AppConfig

class DeptAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dept_admin'

    def ready(self):
        from .admin_sites import register_department_complaints
        register_department_complaints()
