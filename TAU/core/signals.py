from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from core.models import StudentProfile, DepartmentProfile, Department

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_staff:
            default_department, _ = Department.objects.get_or_create(name="General")
            DepartmentProfile.objects.create(user=instance, department=default_department)
        else:
            StudentProfile.objects.create(user=instance, student_id=f"AU{instance.id:04d}")
