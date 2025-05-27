from django.apps import AppConfig
 
class StudentConfig(AppConfig):
    name = 'Student'

    def ready(self):
        from . import signals  # only if signals.py exists
