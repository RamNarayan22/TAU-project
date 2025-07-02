from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from django.contrib.auth.models import User
from core.models import Profile
from io import BytesIO
import openpyxl

# Create your tests here.

class StudentCreationSMSTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a superuser and log in
        self.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        self.client.login(username='admin', password='adminpass')
        # Ensure no user with the test roll number exists
        User.objects.filter(username='240202400999').delete()
        # No need to create the test user here; let the view create it
        Profile.objects.filter(user__username='240202400999').delete()

    @patch('dept_admin.views.send_registration_sms')
    def test_create_student_sends_sms(self, mock_send_sms):
        url = reverse('dept_admin:create_student')
        data = {
            'mode': 'roll',
            'roll_number': '240202400999',
            'first_name': 'Test',
            'last_name': 'Student',
            'phone_number': '9876543210',
        }
        response = self.client.post(url, data, follow=True)
        print('Single student creation response status:', response.status_code)
        print('Single student creation response content:', response.content)
        if not mock_send_sms.called:
            # Try to print form errors from the response context
            if hasattr(response, 'context') and response.context:
                form = response.context.get('form')
                if form:
                    print('Form errors:', form.errors)
        self.assertEqual(response.status_code, 200)
        mock_send_sms.assert_called_once_with('9876543210', 'https://apollouniversity.edu.in/login')
        user = User.objects.get(username='240202400999')
        self.assertEqual(user.profile.phone_number, '9876543210')

    def test_bulk_create_students_sends_sms(self):
        with patch('dept_admin.views.send_registration_sms') as mock_send_sms_view, \
             patch('dept_admin.utils.send_registration_sms') as mock_send_sms_utils:
            url = reverse('dept_admin:create_student')
            # Simulate bulk upload with two students
            import io
            import pandas as pd
            df = pd.DataFrame([
                {'Roll Number': '240202401000', 'First Name': 'Bulk', 'Last Name': 'Student1', 'Phone Number': '9123456789', 'Email': '240202401000@apollouniversity.edu.in'},
                {'Roll Number': '240202401001', 'First Name': 'Bulk', 'Last Name': 'Student2', 'Phone Number': '9234567890', 'Email': '240202401001@apollouniversity.edu.in'},
            ])
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)
            response = self.client.post(url, {
                'mode': 'bulk',
                'excel_file': excel_buffer,
            }, format='multipart', follow=True)
            print('Bulk student creation response status:', response.status_code)
            print('Bulk student creation response content:', response.content)
            # Check that SMS was sent for both students
            mock_send_sms_utils.assert_any_call('9123456789', 'https://apollouniversity.edu.in/login')
            mock_send_sms_utils.assert_any_call('9234567890', 'https://apollouniversity.edu.in/login')
