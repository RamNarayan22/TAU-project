from django import forms
from core.models import Complaint, Department
from .models import DEPARTMENT_CHOICES

class ComplaintForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        empty_label=None,
        required=True
    )
    
    class Meta:
        model = Complaint
        fields = ['department', 'description', 'attachment']
