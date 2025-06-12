from django.contrib.auth.models import User
from core.models import Department, Profile

def setup_general_admin():
    # Get or create the General department
    general_dept, _ = Department.objects.get_or_create(
        name='General',
        defaults={'sla_hours': 24}  # 24-hour SLA for escalated tickets
    )

    # Get the superuser we just created
    user = User.objects.get(username='msd')

    # Create or update their profile
    profile, created = Profile.objects.get_or_create(
        user=user,
        defaults={
            'department': general_dept,
            'is_admin': True,
            'must_change_password': False
        }
    )

    if not created:
        profile.department = general_dept
        profile.is_admin = True
        profile.must_change_password = False
        profile.save()

    print(f"Successfully set up {user.username} as General department admin")

if __name__ == '__main__':
    setup_general_admin() 