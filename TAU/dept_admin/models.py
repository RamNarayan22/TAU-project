from django.db import models
from django.utils import timezone
from core.models import Department

class PendingRegistration(models.Model):
    roll_number = models.CharField(max_length=12, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.roll_number} - {self.email}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['roll_number']),
            models.Index(fields=['is_used', 'expires_at']),
        ] 