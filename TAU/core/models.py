from django.db import models
from django.contrib.auth.models import User
from datetime import datetime


class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Complaint(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('On Hold', 'On Hold'),
        ('Escalated', 'Escalated'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed')
    ]

    ticket_id = models.CharField(max_length=30, unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='core_complaints')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    attachment = models.FileField(upload_to='attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sla_due = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.ticket_id} - {self.title}"


class DepartmentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='core_profile')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.department.name}"


class AuditLog(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='core_auditlogs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.timestamp} - {self.action} on {self.complaint.ticket_id}"
