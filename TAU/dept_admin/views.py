from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from core.models import AuditLog, Profile, Department
from django.contrib.auth.models import User
from django.db import transaction
import string
import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import HttpResponse
import csv
from .forms import UpdateComplaintForm, CreateStudentForm
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.middleware.csrf import rotate_token, get_token
from django.db.models import Avg, Count, Q, F, ExpressionWrapper, fields
import json
from Student.models import Ticket, SLAConfig, SLABreachLog, PRIORITY_CHOICES, TicketUpdate, STATUS_CHOICES
from .utils import create_excel_template, process_excel_file, process_student_registrations, send_registration_sms
from Student.decorators import dept_admin_required
from .decorators import is_dept_admin
from django import forms
from django.urls import reverse
import logging
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm

logger = logging.getLogger('dept_admin')

def is_dept_admin(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.is_admin

def is_superuser(user):
    return user.is_superuser

@ensure_csrf_cookie
@csrf_protect
def login_view(request):
    # Generate CSRF token immediately
    get_token(request)
    
    # If user is already logged in, redirect appropriately
    if request.user.is_authenticated:
        # If student user, log them out and redirect to choose_portal
        if not (request.user.is_superuser or request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.is_admin)):
            logout(request)
            request.session.flush()
            messages.warning(request, 'Students cannot access the department admin portal. Please choose the correct portal below.')
            return redirect('choose_portal')
        # Check if password change is required
        if hasattr(request.user, 'profile') and request.user.profile.must_change_password:
            messages.info(request, 'Please change your password to continue.')
            return redirect('dept_admin:change_password')
            return redirect('dept_admin:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user_obj = User.objects.get(username=username)
            # Check if user is a student before authentication
            if hasattr(user_obj, 'profile') and not user_obj.profile.is_admin:
                messages.error(request, 'Students cannot login to the department admin portal. Please use the student login page.')
                return redirect('student:loginn')
                
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Double check that this is an admin user
                if not (user.is_superuser or user.is_staff or (hasattr(user, 'profile') and user.profile.is_admin)):
                    messages.error(request, 'Students cannot login to the department admin portal. Please use the student login page.')
                    return redirect('student:loginn')
                
                login(request, user)
                # Rotate CSRF token on login
                rotate_token(request)
                # Ensure session is saved
                request.session.save()
                
                # Check if password change is required
                if hasattr(user, 'profile') and user.profile.must_change_password:
                    messages.info(request, 'Please change your password to continue.')
                    return redirect('dept_admin:change_password')
                
                return redirect('dept_admin:dashboard')
            else:
                messages.error(request, 'Incorrect password.')
        except User.DoesNotExist:
            messages.error(request, 'User with this username does not exist.')
    
    # Ensure CSRF token is in the response
    response = render(request, 'dept_admin/login.html')
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=get_token(request),
        max_age=None,
        path=settings.CSRF_COOKIE_PATH,
        domain=settings.CSRF_COOKIE_DOMAIN,
        secure=settings.CSRF_COOKIE_SECURE,
        httponly=settings.CSRF_COOKIE_HTTPONLY,
        samesite=settings.CSRF_COOKIE_SAMESITE
    )
    return response

@login_required
@csrf_protect
def dept_admin_logout(request):
    if request.method == 'POST':
        is_admin = hasattr(request.user, 'profile') and request.user.profile.is_admin
        logout(request)
        request.session.flush()
        messages.success(request, 'You have been successfully logged out.')
        # Redirect to choose_portal after logout
        return redirect('choose_portal')
    logout(request)
    request.session.flush()
    return redirect('choose_portal')  # Default to choose_portal

@login_required
@dept_admin_required
def dashboard(request):
    # Get the department from the user's profile
    department = request.user.profile.department
    department_name = department.name if department else None

    if not department:
        messages.error(request, 'No department assigned to your profile.')
        return redirect('dept_admin:login')

    # Get tickets for the department
    if department.name == 'General':
        # For General department, show all tickets that are either escalated, in progress, or resolved
        tickets = Ticket.objects.filter(
            department=department,
            status__in=['escalated', 'in_progress', 'resolved']
        ).select_related(
            'student',
            'original_department',
            'escalated_by'
        ).order_by('-escalated_at', '-created_at')
    else:
        # For other departments, show their own tickets
        tickets = Ticket.objects.filter(
            department=department
        ).select_related(
            'student'
        ).order_by('-created_at')
    
    # Calculate statistics
    total_tickets = tickets.count()
    escalated_count = tickets.filter(status='escalated').count()
    in_progress_count = tickets.filter(status='in_progress').count()
    resolved_count = tickets.filter(status='resolved').count()
    
    # Calculate SLA metrics
    total_resolved = tickets.filter(status='resolved')
    total_active = tickets.filter(status__in=['escalated', 'in_progress'])
    
    # Calculate resolution rate
    resolution_rate = (resolved_count / total_tickets * 100) if total_tickets > 0 else 0
    
    # Calculate SLA compliance
    sla_compliant = tickets.filter(sla_breach=False).count()
    sla_compliance = (sla_compliant / total_tickets * 100) if total_tickets > 0 else 0
    
    context = {
        'tickets': tickets,
        'department': department,
        'department_name': department_name,
        'total_tickets': total_tickets,
        'escalated_count': escalated_count,
        'in_progress_count': in_progress_count,
        'resolved_count': resolved_count,
        'resolution_rate': resolution_rate,
        'sla_compliance': sla_compliance,
        'is_general_dept': department.name == 'General'
    }
    
    return render(request, 'dept_admin/dashboard.html', context)

@login_required
@dept_admin_required
def view_ticket(request, ticket_id):
    department = request.user.profile.department
    ticket = Ticket.objects.get(id=ticket_id, department=department)
    
    if request.method == 'POST':
        # Handle ticket update
        new_status = request.POST.get('status')
        if new_status:
            ticket.status = new_status
            if new_status == 'in_progress' and not ticket.first_response_at:
                ticket.first_response_at = timezone.now()
            ticket.save()
            messages.success(request, 'Ticket status updated successfully.')
            return redirect('dept_admin:view_ticket', ticket_id=ticket_id)
    
    context = {
        'ticket': ticket
    }
    return render(request, 'dept_admin/view_ticket.html', context)

@login_required
@dept_admin_required
def manage_sla(request):
    department = request.user.profile.department
    
    if request.method == 'POST':
        priority = request.POST.get('priority')
        response_time = int(request.POST.get('response_time'))
        resolution_time = int(request.POST.get('resolution_time'))
        
        sla_config, created = SLAConfig.objects.update_or_create(
            department=department,
            priority=priority,
            defaults={
                'response_time_hours': response_time,
                'resolution_time_hours': resolution_time
            }
        )
        
        if created:
            messages.success(request, f'SLA configuration created for {priority} priority tickets.')
        else:
            messages.success(request, f'SLA configuration updated for {priority} priority tickets.')
        
        return redirect('dept_admin:manage_sla')
    
    sla_configs = SLAConfig.objects.filter(department=department)
    context = {
        'sla_configs': sla_configs,
        'priority_choices': Ticket.PRIORITY_CHOICES
    }
    return render(request, 'dept_admin/manage_sla.html', context)

@login_required
@user_passes_test(is_dept_admin)
def update_complaint(request, complaint_id):
    # Get the ticket
    ticket = get_object_or_404(Ticket, id=complaint_id)
    department = request.user.profile.department

    # Check if user has permission to update this ticket
    if ticket.department != department:
        messages.error(request, 'You do not have permission to update this ticket.')
        return redirect('dept_admin:dashboard')

    if request.method == 'POST':
        form = UpdateComplaintForm(request.POST, instance=ticket)
        if form.is_valid():
            # If this is the General department, don't allow changing certain fields
            if department.name == 'General':
                # Save without changing department or priority
                ticket.status = form.cleaned_data['status']
                if ticket.status == 'resolved':
                    ticket.resolved_at = timezone.now()
                ticket.save(update_fields=['status', 'resolved_at'])
            else:
                ticket = form.save(commit=False)
                if ticket.status == 'resolved':
                    ticket.resolved_at = timezone.now()
                ticket.save()

            # Create ticket update
            TicketUpdate.objects.create(
                ticket=ticket,
                user=request.user,
                comment=f"Status updated to {ticket.get_status_display()}"
            )

            messages.success(request, 'Ticket updated successfully.')
            return redirect('dept_admin:dashboard')
    else:
        form = UpdateComplaintForm(instance=ticket)

    context = {
        'form': form,
        'ticket': ticket,
        'is_general_dept': department.name == 'General'
    }
    return render(request, 'dept_admin/update_complaint.html', context)

@login_required
def export_complaints(request):
    if not request.user.profile.is_admin:
        messages.error(request, 'Access denied. Department admin privileges required.')
        return redirect('dept_admin:login')

    tickets = Ticket.objects.filter(department=request.user.profile.department)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{request.user.profile.department}_tickets.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Ticket ID', 'Student', 'Subject', 'Status', 'Created At'])
    
    for ticket in tickets:
        writer.writerow([
            ticket.ticket_id,
            ticket.student.username if ticket.student else 'Anonymous',
            ticket.subject,
            ticket.status,
            ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

@login_required
@user_passes_test(is_dept_admin)
def dept_sla_dashboard(request):
    department = request.user.profile.department
    
    # Prevent General department from accessing SLA dashboard
    if department.name == 'General':
        messages.error(request, 'The General department does not have access to the SLA dashboard.')
        return redirect('dept_admin:dashboard')
    
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get total tickets
    total_tickets = Ticket.objects.filter(
        department=department,
        created_at__gte=start_date
    ).count()
    
    # Get resolved tickets
    resolved_tickets = Ticket.objects.filter(
        department=department,
        created_at__gte=start_date,
        status='resolved'
    ).count()
    
    resolution_rate = (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0
    
    # Average resolution time
    avg_resolution_time = Ticket.objects.filter(
        department=department,
        created_at__gte=start_date,
        resolved_at__isnull=False
    ).annotate(
        resolution_time=ExpressionWrapper(
            F('resolved_at') - F('created_at'),
            output_field=fields.DurationField()
        )
    ).aggregate(
        avg_time=Avg('resolution_time')
    )['avg_time']
    
    avg_resolution_hours = avg_resolution_time.total_seconds() / 3600 if avg_resolution_time else 0
    
    # SLA breaches
    total_breaches = SLABreachLog.objects.filter(
        ticket__department=department,
        breached_at__gte=start_date
    ).count()
    
    sla_breach_rate = (total_breaches / total_tickets * 100) if total_tickets > 0 else 0
    
    context = {
        'department': department,
        'total_tickets': total_tickets,
        'resolution_rate': round(resolution_rate, 1),
        'avg_resolution_hours': round(avg_resolution_hours, 1),
        'sla_breach_rate': round(sla_breach_rate, 1),
        'days': days
    }
    
    return render(request, 'dept_admin/sla_dashboard.html', context)

@login_required
@user_passes_test(is_dept_admin)
def manage_sla_config(request):
    department = request.user.profile.department
    
    if request.method == 'POST':
        priority = request.POST.get('priority')
        response_time = int(request.POST.get('response_time', 48))
        resolution_time = int(request.POST.get('resolution_time', 48))
        escalation_time = int(request.POST.get('escalation_time', 24))
        
        config, created = SLAConfig.objects.update_or_create(
            department=department,
            priority=priority,
            defaults={
                'response_time_hours': response_time,
                'resolution_time_hours': resolution_time,
                'escalation_time_hours': escalation_time
            }
        )
        
        messages.success(request, 'SLA configuration updated successfully.')
        return redirect('dept_admin:manage_sla_config')
    
    configs = SLAConfig.objects.filter(department=department)
    
    context = {
        'configs': configs,
        'priority_choices': PRIORITY_CHOICES
    }
    
    return render(request, 'dept_admin/manage_sla_config.html', context)

@login_required
@user_passes_test(is_dept_admin)
def sla_breach_report(request):
    department = request.user.profile.department
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get all breaches for the department
    breaches = SLABreachLog.objects.filter(
        ticket__department=department,
        breached_at__gte=start_date
    ).order_by('-breached_at')
    
    # Priority filter
    priority = request.GET.get('priority')
    if priority:
        breaches = breaches.filter(ticket__priority=priority)
    
    context = {
        'breaches': breaches,
        'days': days,
        'priority_choices': PRIORITY_CHOICES,
        'selected_priority': priority
    }
    
    return render(request, 'dept_admin/sla_breach_report.html', context)

@login_required
@user_passes_test(is_superuser)
def create_student(request):
    """Bulk create students - superuser only, no department dependency"""
    if request.method == 'POST':
        # Check if it's a file upload (bulk creation) or form submission (single creation)
        if 'excel_file' in request.FILES:
            # Bulk creation via Excel file
            try:
                created_students, errors = process_excel_file(
                    request.FILES['excel_file'],
                    None  # No department dependency for superuser
                )
                
                if errors:
                    messages.warning(request, 'Some students could not be created:\n' + '\n'.join(errors))
                
                if created_students:
                    messages.success(
                        request,
                        f"Successfully created {len(created_students)} student accounts.\n\n"
                        "Default password for all accounts: Random@123\n"
                        "Students will be required to change their password on first login.\n\n"
                        "Created accounts:\n" +
                        '\n'.join([f"Roll Number: {s['roll_number']}, Name: {s['first_name']} {s['last_name']}, Email: {s['email']}"
                                  for s in created_students])
                    )
        
                return render(request, 'dept_admin/create_student.html', {
                    'preview_data': created_students,
                    'form': CreateStudentForm()
                })
                
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
                return render(request, 'dept_admin/create_student.html', {'form': CreateStudentForm()})
        
        else:
            # Single student creation via form
            form = CreateStudentForm(request.POST)
            if form.is_valid():
                try:
                    email = form.cleaned_data['email']
                    roll_number = email.replace('@apollouniversity.edu.in', '')
                    print(f"[DEBUG] Creating student: roll_number={roll_number}, email={email}, phone={form.cleaned_data['phone_number']}")
                    # Check if user already exists
                    user = User.objects.filter(username=roll_number).first()
                    print(f"[DEBUG] User exists: {user is not None}")
                    if user:
                        # Check if profile already exists for this user
                        if hasattr(user, 'profile'):
                            print("[DEBUG] Profile already exists for user. Skipping creation.")
                            messages.error(request, f"A profile for this student already exists.")
                            form = CreateStudentForm()
                            return render(request, 'dept_admin/create_student.html', {'form': form})
                        else:
                            print("[DEBUG] User exists but no profile. Creating profile.")
                            # User exists but no profile - update user details and create profile
                            user.first_name = form.cleaned_data['first_name']
                            user.last_name = form.cleaned_data['last_name']
                            user.email = email
                            user.save()
                            # Atomically get or create the profile
                            profile, created = Profile.objects.get_or_create(
                                user=user,
                                defaults={
                                    'department': None,  # No department assignment for superuser-created students
                                    'must_change_password': True,
                                    'phone_number': form.cleaned_data['phone_number']
                                }
                            )
                            # Always update phone number and must_change_password
                            profile.phone_number = form.cleaned_data['phone_number']
                            profile.must_change_password = True
                            profile.save()
                            print("[DEBUG] Profile ensured for new user. Sending SMS.")
                            send_registration_sms(form.cleaned_data['phone_number'], 'https://apollouniversity.edu.in/login')
                            messages.success(request, f'Student account created successfully! Roll Number: {roll_number}, Email: {email}')
                            form = CreateStudentForm()
                            return render(request, 'dept_admin/create_student.html', {'form': form})
                    else:
                        print("[DEBUG] Creating new user and profile.")
                        # Create new user without setting password
                        user = User.objects.create(
                            username=roll_number,
                            email=email,
                            first_name=form.cleaned_data['first_name'],
                            last_name=form.cleaned_data['last_name']
                        )
                        # Set password properly using set_password
                        user.set_password('Random@123')
                        user.save()
                        # Atomically get or create the profile
                        profile, created = Profile.objects.get_or_create(
                            user=user,
                            defaults={
                                'department': None,  # No department assignment for superuser-created students
                                'must_change_password': True,
                                'phone_number': form.cleaned_data['phone_number']
                            }
                        )
                        # Always update phone number and must_change_password
                        profile.phone_number = form.cleaned_data['phone_number']
                        profile.must_change_password = True
                        profile.save()
                        print("[DEBUG] Profile ensured for new user. Sending SMS.")
                        send_registration_sms(form.cleaned_data['phone_number'], 'https://apollouniversity.edu.in/login')
                        messages.success(request, f'Student account created successfully! Roll Number: {roll_number}, Email: {email}')
                    form = CreateStudentForm()
                        return render(request, 'dept_admin/create_student.html', {'form': form})
                except forms.ValidationError as e:
                    messages.error(request, str(e))
                except Exception as e:
                    messages.error(request, f'Error creating student account: {str(e)}')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    else:
        form = CreateStudentForm()
    
    return render(request, 'dept_admin/create_student.html', {'form': form})

@login_required
@user_passes_test(is_dept_admin)
def escalate_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, department=request.user.profile.department)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if not reason:
            messages.error(request, 'Please provide a reason for escalation.')
            return redirect('dept_admin:view_ticket', ticket_id=ticket_id)
        
        try:
            ticket.escalate(request.user, reason)
            messages.success(request, f'Ticket {ticket.ticket_id} has been escalated to the General category.')
        except Exception as e:
            messages.error(request, f'Failed to escalate ticket: {str(e)}')
        
        return redirect('dept_admin:dashboard')
    
    return render(request, 'dept_admin/escalate_ticket.html', {'ticket': ticket})

@login_required
@user_passes_test(is_dept_admin)
def view_tickets(request, priority):
    department = request.user.profile.department
    tickets = Ticket.objects.filter(
        department=department,
        priority=priority,
        status__in=['open', 'in_progress', 'on_hold']
    ).order_by('-created_at')
    
    context = {
        'tickets': tickets,
        'priority': priority,
    }
    return render(request, 'dept_admin/ticket_list.html', context)

@login_required
@user_passes_test(is_dept_admin)
def escalate_priority(request, priority):
    department = request.user.profile.department
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if not reason:
            messages.error(request, 'Please provide a reason for escalation.')
            return redirect('dept_admin:view_tickets', priority=priority)
        
        tickets = Ticket.objects.filter(
            department=department,
            priority=priority,
            status__in=['open', 'in_progress', 'on_hold']
        )
        
        escalated_count = 0
        for ticket in tickets:
            try:
                ticket.escalate(request.user, reason)
                escalated_count += 1
            except Exception as e:
                messages.error(request, f'Failed to escalate ticket {ticket.ticket_id}: {str(e)}')
        
        if escalated_count > 0:
            messages.success(request, f'Successfully escalated {escalated_count} {priority} priority tickets.')
        
        return redirect('dept_admin:sla_dashboard')
    
    # Get tickets that would be escalated
    tickets = Ticket.objects.filter(
        department=department,
        priority=priority,
        status__in=['open', 'in_progress', 'on_hold']
    )
    
    context = {
        'tickets': tickets,
        'priority': priority,
    }
    return render(request, 'dept_admin/escalate_priority.html', context)

@login_required
@user_passes_test(is_superuser)
def bulk_create_students(request):
    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'Please upload a file.')
            return render(request, 'dept_admin/bulk_create_students.html')
        
        try:
            file = request.FILES['file']
            
            # Check file type
            if not file.name.endswith(('.xlsx', '.xls')):
                messages.error(request, 'Please upload a valid Excel file (.xlsx or .xls)')
                return render(request, 'dept_admin/bulk_create_students.html')
            
            logger.info(f"Processing uploaded file: {file.name}")
            created_students, errors = process_excel_file(file, None)  # None for department since superuser
            
            if errors:
                for error in errors:
                    messages.warning(request, error)
            
            if created_students:
                success_message = (
                    f"Successfully created {len(created_students)} student accounts.\n\n"
                    "Default password for all accounts: Random@123\n"
                    "Students will be required to change their password on first login.\n\n"
                    "Created accounts:\n" +
                    '\n'.join([f"Roll Number: {s['roll_number']}, Name: {s['first_name']} {s['last_name']}, Email: {s['email']}"
                              for s in created_students])
                )
                messages.success(request, success_message)
                logger.info(f"Successfully created {len(created_students)} students")
            else:
                messages.warning(request, "No students were created. Please check the file format and try again.")
                logger.warning("No students were created from the uploaded file")
    
            return render(request, 'dept_admin/bulk_create_students.html', {
                'preview_data': created_students
            })
            
        except Exception as e:
            error_message = f'Error processing file: {str(e)}'
            messages.error(request, error_message)
            logger.error(error_message)
            return render(request, 'dept_admin/bulk_create_students.html')
    
    return render(request, 'dept_admin/bulk_create_students.html')

@login_required
@user_passes_test(is_superuser)
def download_template(request):
    excel_file = create_excel_template()
    response = HttpResponse(
        excel_file.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=student_template.xlsx'
    return response

@login_required
@user_passes_test(is_dept_admin)
def general_escalated_tickets(request):
    """View for managing all escalated tickets in the General department"""
    if request.user.profile.department.name != 'General':
        messages.error(request, 'You do not have permission to view escalated tickets.')
        return redirect('dept_admin:dashboard')
    
    # Debug information
    print(f"User: {request.user.username}")
    print(f"User department: {request.user.profile.department.name}")
    
    # Get all escalated tickets in the General department
    # Include both escalated status and any tickets that are in General department
    tickets = Ticket.objects.filter(
        department__name='General'
    ).select_related(
        'student',
        'original_department',
        'escalated_by'
    ).order_by('-escalated_at', '-created_at')
    
    # Debug information
    print(f"Total tickets found: {tickets.count()}")
    for ticket in tickets:
        print(f"Ticket: {ticket.ticket_id}, Status: {ticket.status}, Department: {ticket.department.name}")
    
    # Calculate statistics
    total_tickets = tickets.count()
    pending_tickets = tickets.filter(status='escalated').count()
    resolved_tickets = tickets.filter(status='resolved').count()
    in_progress_tickets = tickets.filter(status='in_progress').count()
    
    context = {
        'tickets': tickets,
        'title': 'Escalated Tickets Management',
        'total_tickets': total_tickets,
        'pending_tickets': pending_tickets,
        'resolved_tickets': resolved_tickets,
        'in_progress_tickets': in_progress_tickets,
    }
    
    return render(request, 'dept_admin/general_escalated_tickets.html', context)

@login_required
@user_passes_test(is_dept_admin)
def handle_escalated_ticket(request, ticket_id):
    """View for the General Department to handle an escalated ticket."""
    logger.info(f"=== Starting handle_escalated_ticket for ticket_id: {ticket_id} ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"User: {request.user.username}")
    
    if not request.user.profile.is_general_admin():
        logger.warning(f"User {request.user.username} attempted to access handle_escalated_ticket but is not a general admin")
        messages.error(request, "You do not have permission to access this page.")
        return redirect('dept_admin:dashboard')

    try:
        ticket = get_object_or_404(Ticket, id=ticket_id, department__name='General')
        logger.info(f"Found ticket: {ticket.ticket_id} (Current status: {ticket.status})")
    except Exception as e:
        logger.error(f"Failed to fetch ticket {ticket_id}: {str(e)}")
        messages.error(request, "Ticket not found.")
        return redirect('dept_admin:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        comment = request.POST.get('comment', '')
        logger.info(f"Received POST request with action: {action}")

        if not action:
            logger.warning("No action specified in POST request")
            messages.error(request, "Please specify an action.")
            return redirect('dept_admin:handle_escalated_ticket', ticket_id=ticket.id)

        try:
            with transaction.atomic():
                original_status = ticket.status
                log_action_text = ""

                if action == 'resolve':
                    logger.info("Processing 'resolve' action")
                    ticket.status = 'resolved'
                    ticket.resolved_at = timezone.now()
                    ticket.priority = 'low'
                    log_action_text = f"Ticket marked as Resolved by General Admin."

                elif action == 'in_progress':
                    logger.info("Processing 'in_progress' action")
                    ticket.status = 'in_progress'
                    ticket.resolved_at = None
                    log_action_text = f"Ticket marked as 'In Progress' by General Admin. More time needed."

                elif action == 'return':
                    logger.info("Processing 'return' action")
                    if ticket.original_department:
                        ticket.department = ticket.original_department
                        ticket.status = 'open'
                        ticket.resolved_at = None
                        log_action_text = f"Ticket returned to original department ({ticket.original_department.name}) by General Admin."
                    else:
                        logger.error("Cannot return ticket - no original department recorded")
                        messages.error(request, "Cannot return ticket as original department is not recorded.")
                        return redirect('dept_admin:handle_escalated_ticket', ticket_id=ticket.id)
                
                logger.info(f"Saving ticket with new status: {ticket.status}")
                ticket.save()
                logger.info("Ticket saved successfully")

                # Create ticket update
                TicketUpdate.objects.create(
                    ticket=ticket,
                    user=request.user,
                    comment=f"{log_action_text}\nAdmin comment: {comment}" if comment else log_action_text,
                    is_internal=True
                )

                messages.success(request, log_action_text)
                return redirect('dept_admin:dashboard')

        except Exception as e:
            logger.error(f"Error handling ticket: {str(e)}")
            messages.error(request, f"Failed to handle ticket: {str(e)}")
            return redirect('dept_admin:handle_escalated_ticket', ticket_id=ticket.id)

    # Get ticket updates for display
    updates = TicketUpdate.objects.filter(ticket=ticket).order_by('-created_at')

    context = {
        'ticket': ticket,
        'title': f'Handle Escalated Ticket: {ticket.ticket_id}',
        'updates': updates,
    }
    return render(request, 'dept_admin/handle_escalated_ticket.html', context)

@login_required
@user_passes_test(is_dept_admin)
def profile_view(request):
    """View for managing user profile"""
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        # Handle profile update
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if email:
            user.email = email
        
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('dept_admin:profile')

    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'dept_admin/profile.html', context)

@login_required
@user_passes_test(is_dept_admin)
def settings_view(request):
    """View for managing user settings"""
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        # Handle password change
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if current_password and new_password and confirm_password:
            if user.check_password(current_password):
                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, 'Password changed successfully. Please login again.')
                    return redirect('dept_admin:login')
                else:
                    messages.error(request, 'New passwords do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')

    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'dept_admin/settings.html', context)

@login_required
@user_passes_test(is_dept_admin)
def change_password(request):
    # If password change is not required, redirect to dashboard
    if not request.user.profile.must_change_password:
        return redirect('dept_admin:dashboard')

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            
            profile = request.user.profile
            profile.must_change_password = False
            profile.save()

            messages.success(request, 'Your password was successfully updated!')
            return redirect('dept_admin:dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'dept_admin/change_password.html', {'form': form})
