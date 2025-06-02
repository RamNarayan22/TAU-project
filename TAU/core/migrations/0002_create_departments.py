from django.db import migrations

def create_departments(apps, schema_editor):
    Department = apps.get_model('core', 'Department')
    departments = [
        'Finance',
        'Hostel',
        'Gatepass',
        'Academics',
        'Others'
    ]
    for dept_name in departments:
        Department.objects.create(name=dept_name)

def reverse_departments(apps, schema_editor):
    Department = apps.get_model('core', 'Department')
    Department.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_remove_studentprofile_user_remove_auditlog_notes_and_more'),
    ]

    operations = [
        migrations.RunPython(create_departments, reverse_departments),
    ] 