from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

DEPARTMENT_CHOICES = [
    ('Finance', 'Finance'),
    ('Hostel', 'Hostel'),
    ('Mess', 'Mess'),
    ('Academics', 'Academics'),
    ('Others', 'Others'),
    ('Gate Pass', 'Gate Pass'),
]

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    sla_hours = models.IntegerField(default=48)  # Default SLA time in hours

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        
    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        if self.name.lower() == 'gate pass':
            self.name = 'Gate Pass'
        super().save(*args, **kwargs)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    is_admin = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # New field for student mobile number

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def is_general_admin(self):
        """Check if the user is an admin of the General department."""
        return self.is_admin and self.department and self.department.name == 'General'

class Complaint(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Rejected', 'Rejected'),
    ]

    ticket_id = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            prefix = self.department.name[:3].upper()
            latest = Complaint.objects.filter(department=self.department).order_by('-id').first()
            next_id = 1
            if latest and latest.ticket_id:
                try:
                    last_num = int(latest.ticket_id.split('-')[-1])
                    next_id = last_num + 1
                except ValueError:
                    pass
            self.ticket_id = f"{prefix}-{next_id:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.department}"

class AuditLog(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=255)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Audit: {self.action} on {self.complaint.ticket_id} by {self.performed_by}"
