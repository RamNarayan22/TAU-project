from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import DepartmentProfile, StudentProfile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_staff:
            DepartmentProfile.objects.get_or_create(user=instance)
        else:
            StudentProfile.objects.get_or_create(user=instance, student_id=f"AU{instance.id:04d}")
    else:
        if not instance.is_staff:
            try:
                instance.core_student_profile.save()   # <-- change here!
            except StudentProfile.DoesNotExist:
                StudentProfile.objects.create(user=instance, student_id=f"AU{instance.id:04d}")
        else:
            try:
                instance.core_profile.save()           # <-- also change here if needed!
            except DepartmentProfile.DoesNotExist:
                DepartmentProfile.objects.create(user=instance)

