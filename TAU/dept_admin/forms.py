from django import forms
from core.models import Department
from Student.models import Ticket
from django.contrib.auth.models import User


class CreateStudentForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    roll_number = forms.CharField(max_length=20, required=True)

    def clean_roll_number(self):
        roll_number = self.cleaned_data.get('roll_number')
        if not roll_number.isdigit() or len(roll_number) != 12:
            raise forms.ValidationError("Roll number must be exactly 12 digits")
        if User.objects.filter(username=roll_number).exists():
            raise forms.ValidationError("A student with this roll number already exists.")
        return roll_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        if not email.endswith('@theapollouniversity.edu.in'):
            raise forms.ValidationError("Please use a valid university email address (@theapollouniversity.edu.in)")
        return email


class UpdateComplaintForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['status', 'priority']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'})
        }
