from django import forms
from core.models import Department
from Student.models import Ticket
from django.contrib.auth.models import User


class CreateStudentForm(forms.Form):
    MODE_CHOICES = [
        ('email', 'Enter Full Email'),
        ('roll', 'Enter 12-digit Roll Number'),
    ]
    mode = forms.ChoiceField(
        choices=MODE_CHOICES,
        widget=forms.RadioSelect,
        initial='email',
        required=True,
        label='Input Method'
    )
    email = forms.EmailField(
        required=False,
        label='Email (Roll Number)',
        help_text='Enter roll number with @apollouniversity.edu.in (e.g., 240202400001@apollouniversity.edu.in)',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '240202400001@apollouniversity.edu.in'
        })
    )
    roll_number = forms.CharField(
        required=False,
        max_length=12,
        min_length=12,
        label='12-digit Roll Number',
        help_text='Enter only the 12-digit roll number (e.g., 240202400001)',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '240202400001'
        })
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter last name'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        label='Phone Number',
        help_text='Enter a valid 10-digit mobile number',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '9876543210'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get('mode')
        email = cleaned_data.get('email')
        roll_number = cleaned_data.get('roll_number')
        phone_number = cleaned_data.get('phone_number')
        from django.contrib.auth.models import User
        from core.models import Profile
        
        if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
            self.add_error('phone_number', 'Enter a valid 10-digit mobile number.')
        
        if mode == 'email':
            if not email:
                self.add_error('email', 'This field is required.')
            else:
                if not email.endswith('@apollouniversity.edu.in'):
                    self.add_error('email', 'Email must end with @apollouniversity.edu.in')
                roll_number_val = email.replace('@apollouniversity.edu.in', '')
                if not roll_number_val.isdigit() or len(roll_number_val) != 12:
                    self.add_error('email', 'Roll number must be exactly 12 digits before @apollouniversity.edu.in')
        
                # Check if user exists and has a profile
                user = User.objects.filter(username=roll_number_val).first()
                if user and hasattr(user, 'profile'):
                    self.add_error('email', 'A student with this roll number already exists.')
        elif mode == 'roll':
            if not roll_number:
                self.add_error('roll_number', 'This field is required.')
            else:
                if not roll_number.isdigit() or len(roll_number) != 12:
                    self.add_error('roll_number', 'Roll number must be exactly 12 digits.')
                email_val = f"{roll_number}@apollouniversity.edu.in"
                # Check if user exists and has a profile
                user = User.objects.filter(username=roll_number).first()
                if user and hasattr(user, 'profile'):
                    self.add_error('roll_number', 'A student with this roll number already exists.')
                cleaned_data['email'] = email_val
        return cleaned_data

    def generate_unique_roll_number(self, department):
        """Generate a unique roll number for the given department."""
        max_attempts = 50  # Increased from 10 to handle more edge cases
        
        # Get all existing numeric usernames and find the highest one
        existing_users = User.objects.filter(username__regex=r'^\d{12}$').values_list('username', flat=True)
        
        if existing_users:
            # Convert to integers and find the maximum
            try:
                max_number = max(int(username) for username in existing_users)
                next_number = max_number + 1
            except (ValueError, TypeError):
                # If conversion fails, start from a base number
                from django.utils import timezone
                next_number = int(f"{department.id:02d}{timezone.now().year}00000001")
        else:
            # No existing users with numeric usernames, start from base
            from django.utils import timezone
            next_number = int(f"{department.id:02d}{timezone.now().year}00000001")
        
        # Try to find a unique roll number
        for attempt in range(max_attempts):
            roll_number = f"{next_number:012d}"
            
            # Check if this roll number is already taken
            if not User.objects.filter(username=roll_number).exists():
                return roll_number
            
            # If taken, try the next number
            next_number += 1
        
        # If we still can't find a unique number, try a fallback approach
        import random
        timestamp = int(timezone.now().timestamp())
        random_suffix = random.randint(1000, 9999)
        fallback_number = int(f"{department.id:02d}{timestamp % 100000000}{random_suffix}")
        
        for fallback_attempt in range(10):
            fallback_roll_number = f"{fallback_number:012d}"
            if not User.objects.filter(username=fallback_roll_number).exists():
                return fallback_roll_number
            fallback_number += 1
        
        raise forms.ValidationError("Unable to generate a unique roll number. Please try again.")


class UpdateComplaintForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['status', 'priority']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'})
        }
