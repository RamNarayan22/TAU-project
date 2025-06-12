from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from core.models import Profile
from django.utils import timezone
from .models import TicketUpdate, Ticket

# Signal handlers have been moved to core.signals
# This file is kept for future student-specific signals if needed

@receiver(post_save, sender=TicketUpdate)
def update_ticket_response_time(sender, instance, created, **kwargs):
    if created and not instance.is_internal:
        ticket = instance.ticket
        # If this is the first response and it's not from the student
        if not ticket.first_response_at and instance.user != ticket.student:
            ticket.first_response_at = instance.created_at
            ticket.save()

@receiver(pre_save, sender=Ticket)
def update_resolution_time(sender, instance, **kwargs):
    if instance.status == 'resolved' and not instance.resolved_at:
        instance.resolved_at = timezone.now()
    elif instance.status != 'resolved':
        instance.resolved_at = None
