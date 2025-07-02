import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TAU.settings')

import django
django.setup()

from django.test import Client, override_settings
from django.contrib.auth.models import User
from core.models import Profile
from django.core.files.uploadedfile import SimpleUploadedFile

@override_settings(ALLOWED_HOSTS=['testserver'])
def test_bulk_upload():
    print("\n=== Testing Bulk Upload of AP Students ===\n")
    
    # Create a superuser if not exists
    superuser = User.objects.filter(username='admin').first()
    if not superuser:
        superuser = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Created superuser: admin/admin123")
    
    # Create test client
    client = Client()
    
    # Login
    login_success = client.login(username='admin', password='admin123')
    if not login_success:
        print("Failed to login!")
        return
    
    print("Logged in as superuser")
    
    # Get initial counts (only student users)
    initial_users = User.objects.filter(username__startswith='24020240').count()
    initial_profiles = Profile.objects.filter(user__username__startswith='24020240').count()
    print(f"\nInitial counts (students only):")
    print(f"Student users: {initial_users}")
    print(f"Student profiles: {initial_profiles}")
    
    # Open and upload the file
    file_path = 'ap_students.xlsx'
    if not os.path.exists(file_path):
        print(f"\nError: {file_path} not found!")
        return
        
    with open(file_path, 'rb') as f:
        file_data = f.read()
        uploaded_file = SimpleUploadedFile(
            name=file_path,
            content=file_data,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response = client.post('/department/bulk-create-students/', {
            'file': uploaded_file
        }, HTTP_HOST='testserver')
    
    # Check response
    print(f"\nUpload response status: {response.status_code}")
    if hasattr(response, 'content'):
        print(f"Response content: {response.content.decode()}")
    
    # Get final counts (only student users)
    final_users = User.objects.filter(username__startswith='24020240').count()
    final_profiles = Profile.objects.filter(user__username__startswith='24020240').count()
    print(f"\nFinal counts (students only):")
    print(f"Student users: {final_users}")
    print(f"Student profiles: {final_profiles}")
    print(f"New student users created: {final_users - initial_users}")
    print(f"New student profiles created: {final_profiles - initial_profiles}")
    
    # Verify some of the created users
    print("\nVerifying created users:")
    for roll_number in ['240202400001', '240202400005', '240202400010']:
        user = User.objects.filter(username=roll_number).first()
        if user:
            profile = Profile.objects.filter(user=user).first()
            print(f"\nUser: {roll_number}")
            print(f"Name: {user.first_name} {user.last_name}")
            print(f"Email: {user.email}")
            print(f"Profile exists: {profile is not None}")
            print(f"Must change password: {profile.must_change_password if profile else 'N/A'}")
        else:
            print(f"\nUser {roll_number} not found!")

if __name__ == '__main__':
    test_bulk_upload() 