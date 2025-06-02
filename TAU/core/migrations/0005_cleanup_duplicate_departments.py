from django.db import migrations

def cleanup_departments(apps, schema_editor):
    Department = apps.get_model('core', 'Department')
    
    # Get all departments
    departments = Department.objects.all()
    
    # Keep track of seen names
    seen_names = {}
    
    # Iterate through departments
    for dept in departments:
        name = dept.name.strip()
        # Normalize Gate Pass
        if name.lower() == 'gate pass':
            name = 'Gate Pass'
            
        if name in seen_names:
            # If we've seen this name before, update any foreign keys to point to the first instance
            # and delete this duplicate
            original_dept = seen_names[name]
            
            # Update Profile FKs
            Profile = apps.get_model('core', 'Profile')
            Profile.objects.filter(department=dept).update(department=original_dept)
            
            # Update Complaint FKs
            Complaint = apps.get_model('core', 'Complaint')
            Complaint.objects.filter(department=dept).update(department=original_dept)
            
            # Delete the duplicate
            dept.delete()
        else:
            # First time seeing this name
            seen_names[name] = dept
            # Update name if needed
            if dept.name != name:
                dept.name = name
                dept.save()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_remove_studentprofile_user_remove_auditlog_notes_and_more'),
    ]

    operations = [
        migrations.RunPython(cleanup_departments),
    ] 