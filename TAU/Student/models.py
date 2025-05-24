from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models, transaction, IntegrityError


class Complaint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

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
    ticket_id = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            prefix = self.department[:3].upper()
            for count in range(1, 10000):  # e.g., FIN001 to FIN9999
                potential_id = f"{prefix}{count:03}"
                if not Complaint.objects.filter(ticket_id=potential_id).exists():
                    self.ticket_id = potential_id
                    break

        try:
            with transaction.atomic():
                super().save(*args, **kwargs)
        except IntegrityError:
            self.ticket_id = None  # Retry generation
            return self.save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.department}"
