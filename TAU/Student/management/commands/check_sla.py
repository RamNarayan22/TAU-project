from django.core.management.base import BaseCommand
from django.utils import timezone
from Student.models import Ticket, SLABreachLog
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Check for SLA breaches and escalations, and send notifications'

    def handle(self, *args, **options):
        # Get system admin user for automatic escalations
        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            self.stdout.write(
                self.style.ERROR('No superuser found for automatic escalations')
            )
            return

        # Get all open tickets
        open_tickets = Ticket.objects.filter(
            status__in=['open', 'in_progress', 'on_hold']
        )

        for ticket in open_tickets:
            # Check for SLA breach
            if ticket.is_sla_breached and not ticket.sla_breach:
                # Create SLA breach log
                breach_type = 'response' if not ticket.first_response_at else 'resolution'
                breach_log = SLABreachLog.objects.create(
                    ticket=ticket,
                    breach_type=breach_type
                )

                # Update ticket status
                ticket.sla_breach = True
                ticket.save()

                # Send notification email
                subject = f'SLA Breach Alert - Ticket {ticket.ticket_id}'
                message = f'''
                SLA breach detected for ticket {ticket.ticket_id}
                Department: {ticket.department}
                Priority: {ticket.priority}
                Created: {ticket.created_at}
                Breach Type: {breach_type}
                
                Please take immediate action.
                '''
                
                # Send to department head
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [f"{ticket.department.name.lower()}@apollouniversity.edu"],
                        fail_silently=False,
                    )
                    breach_log.notified = True
                    breach_log.save()
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to send notification for ticket {ticket.ticket_id}: {str(e)}')
                    )

            # Check for escalation
            if ticket.should_escalate() and ticket.status != 'escalated':
                try:
                    ticket.escalate(
                        system_user,
                        reason="Automatic escalation due to SLA breach"
                    )
                    
                    # Send escalation notification
                    subject = f'Ticket Escalated - {ticket.ticket_id}'
                    message = f'''
                    Ticket {ticket.ticket_id} has been automatically escalated to the General category.
                    
                    Original Department: {ticket.original_department}
                    Current Department: {ticket.department}
                    Priority: {ticket.priority}
                    Created: {ticket.created_at}
                    Escalated: {ticket.escalated_at}
                    
                    This ticket requires immediate attention from the general support team.
                    '''
                    
                    # Send to both original department and general support
                    recipients = [
                        f"{ticket.original_department.name.lower()}@apollouniversity.edu",
                        "general.support@apollouniversity.edu"
                    ]
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        recipients,
                        fail_silently=False,
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully escalated ticket {ticket.ticket_id}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to escalate ticket {ticket.ticket_id}: {str(e)}')
                    )

        self.stdout.write(
            self.style.SUCCESS('Successfully checked SLA breaches and escalations')
        ) 