from django import forms
from core.models import Complaint

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['description', 'department', 'attachment']  # no title field here as per your model
