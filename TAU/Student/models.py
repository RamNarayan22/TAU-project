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
