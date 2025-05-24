from django import forms
from .models import Complaint
from django.db import models


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['department', 'description', 'attachment']

