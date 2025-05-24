from django.db import models
from django.contrib.auth.models import User

STATUS_CHOICES = (
    ('Pending', 'Pending'),
    ('In Progress', 'In Progress'),
    ('Resolved', 'Resolved'),
)

DEPARTMENT_CHOICES = (
    ('Finance', 'Finance'),
    ('Hostel', 'Hostel'),
    ('Mess', 'Mess'),
    ('Academics', 'Academics'),
    ('Others', 'Others'),
)

class Complaint(models.Model):
    ticket_id = models.CharField(max_length=20, unique=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticket_id} - {self.department} - {self.status}"
