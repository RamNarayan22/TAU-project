from django.db import migrations

def initialize_departments(apps, schema_editor):
    Department = apps.get_model('core', 'Department')
    
    # Define the departments we want to have (Gate Pass appears only once)
    departments = [
        'Academics',
        'Finance',
        'Gate Pass',
        'Hostel',
        'Mess',
        'Others'
    ]
    
    # First, remove any existing departments
    Department.objects.all().delete()
    
    # Create the departments fresh
    for dept_name in departments:
        Department.objects.create(name=dept_name)

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(initialize_departments),
    ] 