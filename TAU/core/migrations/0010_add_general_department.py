from django.db import migrations

def add_general_department(apps, schema_editor):
    Department = apps.get_model('core', 'Department')
    Department.objects.get_or_create(
        name='General',
        defaults={'sla_hours': 24}  # Setting a shorter SLA time for escalated tickets
    )

def remove_general_department(apps, schema_editor):
    Department = apps.get_model('core', 'Department')
    Department.objects.filter(name='General').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0009_department_sla_hours'),
    ]

    operations = [
        migrations.RunPython(add_general_department, remove_general_department),
    ] 