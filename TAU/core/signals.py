from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import StudentProfile, DepartmentProfile

@receiver(post_save, sender=User)
def create_profiles(sender, instance, created, **kwargs):
    if created:
        if instance.is_staff:
            DepartmentProfile.objects.create(user=instance)
        else:
            StudentProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profiles(sender, instance, **kwargs):
    if hasattr(instance, 'studentprofile'):
        instance.studentprofile.save()
    if hasattr(instance, 'departmentprofile'):
        instance.departmentprofile.save()
