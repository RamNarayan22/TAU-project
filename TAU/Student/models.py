from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models

class Complaint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # ← Add this line

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]

    department = models.CharField(max_length=50, choices=[
        ('Finance', 'Finance'),
        ('Hostel', 'Hostel'),
        ('Mess', 'Mess'),
        ('Academics', 'Academics'),
        ('Others', 'Others'),
    ])
    description = models.TextField()
    attachment = models.ImageField(upload_to='attachments/', null=True, blank=True)
    ticket_id = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)  # for recent_complaints sort

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            prefix = self.department[:3].upper()
            count = Complaint.objects.filter(department=self.department).count() + 1
            self.ticket_id = f"{prefix}{count:03}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.department}"
