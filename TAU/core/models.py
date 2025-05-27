from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

DEPARTMENT_CHOICES = [
    ('Finance', 'Finance'),
    ('Hostel', 'Hostel'),
    ('Mess', 'Mess'),
    ('Academics', 'Academics'),
    ('Others', 'Others'),
    ('Gate Pass', 'Gate Pass'),
]

STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('In Progress', 'In Progress'),
    ('Resolved', 'Resolved'),
    ('Rejected', 'Rejected'),
]

class Complaint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='complaints')
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    description = models.TextField()
    ticket_id = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            prefix = self.department[:3].upper()
            for count in range(1, 10000):
                potential_id = f"{prefix}{count:03}"
                if not Complaint.objects.filter(ticket_id=potential_id).exists():
                    self.ticket_id = potential_id
                    break
        from django.db import transaction, IntegrityError
        try:
            with transaction.atomic():
                super().save(*args, **kwargs)
        except IntegrityError:
            # retry once to avoid infinite recursion
            if not getattr(self, '_retrying', False):
                self._retrying = True
                self.ticket_id = None
                self.save(*args, **kwargs)
            else:
                raise

    def __str__(self):
        return f"{self.ticket_id} - {self.department}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, null=True, blank=True)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} Profile"
        

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()
