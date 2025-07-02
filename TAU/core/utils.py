from Student.models import Ticket
from datetime import timedelta, datetime
from django.core.mail import send_mail

def generate_ticket_id(department_name):
    prefix = department_name[:3].upper()
    count = Ticket.objects.filter(department__name=department_name).count() + 1
    return f"AU-2025-{prefix}-{count:04d}"

def calculate_sla_due():
    return datetime.now() + timedelta(days=2)

def send_status_notification(ticket):
    message = f"""
    Hello {ticket.student.first_name},

    Your ticket (Ticket ID: {ticket.ticket_id}) has been updated.
    Current Status: {ticket.status}

    Regards,
    Apollo University Support Team
    """
    send_mail(
        subject=f"Update on Ticket {ticket.ticket_id}",
        message=message,
        from_email='no-reply@apollo.edu',
        recipient_list=[ticket.student.email],
        fail_silently=True,
    )
