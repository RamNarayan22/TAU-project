from .models import Complaint
from datetime import timedelta, datetime
from django.core.mail import send_mail

def generate_ticket_id(department_name):
    prefix = department_name[:3].upper()
    count = Complaint.objects.filter(department__name=department_name).count() + 1
    return f"AU-2025-{prefix}-{count:04d}"

def calculate_sla_due():
    return datetime.now() + timedelta(days=2)

def send_status_notification(complaint):
    message = f"""
    Hello {complaint.user.first_name},

    Your complaint (Ticket ID: {complaint.ticket_id}) has been updated.
    Current Status: {complaint.status}

    Regards,
    Apollo University Support Team
    """
    send_mail(
        subject=f"Update on Ticket {complaint.ticket_id}",
        message=message,
        from_email='no-reply@apollo.edu',
        recipient_list=[complaint.user.email],
        fail_silently=True,
    )
