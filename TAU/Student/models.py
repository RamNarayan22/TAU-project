from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import uuid
from core.models import Department
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings
import os

PRIORITY_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('urgent', 'Urgent'),
]

STATUS_CHOICES = [
    ('open', 'Open'),
    ('in_progress', 'In Progress'),
    ('on_hold', 'On Hold'),
    ('escalated', 'Escalated'),
    ('resolved', 'Resolved'),
    ('closed', 'Closed'),
]

def validate_file_size(value):
    filesize = value.size
    if filesize > 5 * 1024 * 1024:  # 5MB
        raise ValidationError("The maximum file size that can be uploaded is 5MB")

class SLAConfig(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    response_time_hours = models.IntegerField(
        default=8,  # Default 8 hours for response
        help_text="Maximum time in hours to first response"
    )
    resolution_time_hours = models.IntegerField(
        default=24,  # Default 24 hours for resolution
        help_text="Maximum time in hours to resolve the ticket"
    )
    escalation_time_hours = models.IntegerField(
        default=24,  # Default 24 hours for escalation
        help_text="Time in hours after which the ticket should be escalated"
    )

    class Meta:
        unique_together = ['department', 'priority']
        verbose_name = "SLA Configuration"
        verbose_name_plural = "SLA Configurations"

    def __str__(self):
        return f"{self.department.name} - {self.get_priority_display()} Priority SLA"

    def save(self, *args, **kwargs):
        if not self.response_time_hours:
            self.response_time_hours = 8
        if not self.resolution_time_hours:
            self.resolution_time_hours = 24
        if not self.escalation_time_hours:
            self.escalation_time_hours = 24
        super().save(*args, **kwargs)

class Ticket(models.Model):
    ticket_id = models.CharField(max_length=20, unique=True, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_tickets')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    sla_breach = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True)
    escalated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='escalated_tickets')
    escalation_reason = models.TextField(null=True, blank=True)
    original_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='original_tickets')
    attachment = models.FileField(
        upload_to='ticket_attachments/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png']
            ),
            validate_file_size
        ]
    )
    
    def save(self, *args, **kwargs):
        if not self.ticket_id:
            year = timezone.now().strftime('%Y')
            dept_code = self.department.name[:3].upper()
            random_id = str(uuid.uuid4()).upper()[:4]
            self.ticket_id = f'AU-{year}-{dept_code}-{random_id}'
        
        # Store original department when escalating
        if self.status == 'escalated' and not self.escalated_at:
            self.escalated_at = timezone.now()
            if not self.original_department:
                self.original_department = self.department
        
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status != 'resolved':
            self.resolved_at = None
            self.resolved_by = None
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.ticket_id

    @property
    def is_sla_breached(self):
        if self.status in ['resolved', 'closed']:
            return False
        
        sla_config = SLAConfig.objects.get(
            department=self.department,
            priority=self.priority
        )
        
        # Check response time SLA
        if not self.first_response_at:
            time_since_creation = timezone.now() - self.created_at
            if time_since_creation.total_seconds() / 3600 > sla_config.response_time_hours:
                return True
        
        # Check resolution time SLA
        time_since_creation = timezone.now() - self.created_at
        if time_since_creation.total_seconds() / 3600 > sla_config.resolution_time_hours:
            return True
            
        return False

    def should_escalate(self):
        """Check if the ticket should be escalated based on SLA configuration"""
        if self.status in ['resolved', 'closed', 'escalated']:
            return False

        sla_config = SLAConfig.objects.get(
            department=self.department,
            priority=self.priority
        )

        time_since_creation = timezone.now() - self.created_at
        return time_since_creation.total_seconds() / 3600 > sla_config.escalation_time_hours

    def escalate(self, escalated_by, reason=None):
        """Escalate the ticket to general category"""
        if self.status != 'escalated':
            # Store the original department before changing it
            self.original_department = self.department
            
            # Get or create the General department
            general_dept, _ = Department.objects.get_or_create(
                name='General',
                defaults={'sla_hours': 24}  # 24-hour SLA for escalated tickets
            )
            
            # Update ticket fields
            self.department = general_dept
            self.status = 'escalated'
            self.escalated_at = timezone.now()
            self.escalated_by = escalated_by
            self.escalation_reason = reason
            # Save all fields without update_fields restriction to ensure proper update
            self.save()

            # Create ticket update for escalation
            TicketUpdate.objects.create(
                ticket=self,
                user=escalated_by,
                comment=f"Ticket escalated to General department. Reason: {reason or 'SLA breach'}",
                is_internal=True
            )

            # Log the escalation
            from django.contrib.admin.models import LogEntry, CHANGE
            from django.contrib.contenttypes.models import ContentType
            LogEntry.objects.create(
                user_id=escalated_by.id,
                content_type_id=ContentType.objects.get_for_model(self).id,
                object_id=self.id,
                object_repr=str(self),
                action_flag=CHANGE,
                change_message=f"Ticket escalated to General department. Reason: {reason or 'SLA breach'}"
            )

    def clean(self):
        super().clean()
        if self.attachment:
            # Additional validation can be added here if needed
            pass

    class Meta:
        ordering = ['-created_at']

class TicketUpdate(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='updates')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_internal = models.BooleanField(default=False)  # For internal staff notes

    def __str__(self):
        return f"Update on {self.ticket.ticket_id} by {self.user.username}"

class SLABreachLog(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    breach_type = models.CharField(max_length=20, choices=[
        ('response', 'Response Time'),
        ('resolution', 'Resolution Time'),
    ])
    breached_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    def __str__(self):
        return f"SLA Breach - {self.ticket.ticket_id} - {self.breach_type}"
