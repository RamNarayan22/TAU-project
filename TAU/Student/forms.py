from django import forms
from django.db.models import Min
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from core.models import Complaint, Department
from .models import DEPARTMENT_CHOICES

class StudentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name',
            'minlength': '2',
            'oninput': 'this.value = this.value.trim()',
            'autocomplete': 'given-name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name',
            'minlength': '2',
            'oninput': 'this.value = this.value.trim()',
            'autocomplete': 'family-name'
        })
    )
    
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'oninput': 'this.value = this.value.trim()',
            'autocomplete': 'email'
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a strong password',
            'minlength': '8',
            'id': 'password1',
            'name': 'password1',
            'oninput': 'validateForm()',
            'autocomplete': 'new-password'
        })
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'minlength': '8',
            'id': 'password2',
            'name': 'password2',
            'oninput': 'validateForm()',
            'autocomplete': 'new-password'
        })
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if not password1:
            self.add_error('password1', 'Password is required.')
        if not password2:
            self.add_error('password2', 'Password confirmation is required.')
            
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'The two password fields must match.')
            
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class ComplaintForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=None,  # We'll set this in __init__
        empty_label="Select Department",
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'aria-label': 'Department Selection'
        })
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Please describe your complaint in detail',
            'rows': 4
        }),
        required=True
    )
    
    attachment = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get unique departments by using subquery to get the first ID for each name
        unique_dept_ids = Department.objects.values('name').annotate(
            min_id=Min('id')
        ).values_list('min_id', flat=True)
        self.fields['department'].queryset = Department.objects.filter(
            id__in=unique_dept_ids
        ).order_by('name')
    
    class Meta:
        model = Complaint
        fields = ['department', 'description', 'attachment']
        
    def clean_department(self):
        department = self.cleaned_data.get('department')
        if not department:
            raise forms.ValidationError("Please select a department")
        return department
        
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError("Please provide a description of your complaint")
        if len(description) < 10:
            raise forms.ValidationError("Description must be at least 10 characters long")
        return description
