from django.db import migrations

def create_default_departments(apps, schema_editor):
    Department = apps.get_model('core', 'Department')
    departments = [
        'Finance',
        'Hostel',
        'Mess',
        'Academics',
        'Others',
        'Gate Pass'
    ]
    for dept_name in departments:
        Department.objects.get_or_create(name=dept_name)

def remove_default_departments(apps, schema_editor):
    Department = apps.get_model('core', 'Department')
    Department.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_departments, remove_default_departments),
    ] 