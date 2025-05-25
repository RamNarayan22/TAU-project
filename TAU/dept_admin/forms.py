from django import forms
from core.models import Complaint

class UpdateComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['status']