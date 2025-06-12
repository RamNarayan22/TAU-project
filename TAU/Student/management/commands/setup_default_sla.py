from django.core.management.base import BaseCommand
from Student.models import Department, SLAConfig

class Command(BaseCommand):
    help = 'Sets up default SLA configurations for all departments'

    def handle(self, *args, **options):
        # Default SLA configurations for each priority level
        default_slas = {
            'urgent': {'response': 1, 'resolution': 4},    # 1 hour response, 4 hours resolution
            'high': {'response': 4, 'resolution': 8},      # 4 hours response, 8 hours resolution
            'medium': {'response': 8, 'resolution': 24},   # 8 hours response, 24 hours resolution
            'low': {'response': 24, 'resolution': 48},     # 24 hours response, 48 hours resolution
        }
        
        departments = Department.objects.all()
        created_count = 0
        
        for department in departments:
            for priority, times in default_slas.items():
                sla_config, created = SLAConfig.objects.get_or_create(
                    department=department,
                    priority=priority,
                    defaults={
                        'response_time_hours': times['response'],
                        'resolution_time_hours': times['resolution']
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created SLA config for {department.name} - {priority} priority'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} SLA configurations'
            )
        ) 