from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

DEPARTMENT_CHOICES = [
    ('Finance', 'Finance'),
    ('Hostel', 'Hostel'),
    ('Gatepass', 'Gatepass'),
    ('Academics', 'Academics'),
    ('Others', 'Others'),
]


class Department(models.Model):
    name = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES)

    def __str__(self):
        return self.name


class Complaint(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='student_complaints')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    description = models.TextField()
    ticket_id = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            prefix = self.department.name[:3].upper()
            for count in range(1, 10000):
                potential_id = f"{prefix}{count:03}"
                if not Complaint.objects.filter(ticket_id=potential_id).exists():
                    self.ticket_id = potential_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.department.name}"
