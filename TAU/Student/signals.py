from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from core.models import Profile

# Signal handlers have been moved to core.signals
# This file is kept for future student-specific signals if needed
