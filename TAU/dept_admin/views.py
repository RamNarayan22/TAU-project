from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from core.models import AuditLog, Profile
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
from Student.models import Ticket, Department, SLAConfig, SLABreachLog, PRIORITY_CHOICES, TicketUpdate, STATUS_CHOICES
from .utils import create_excel_template, process_excel_file
from Student.decorators import dept_admin_required
from .decorators import is_dept_admin

def is_dept_admin(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.is_admin

def is_superuser(user):
    return user.is_superuser

@ensure_csrf_cookie
def login_view(request):
    # If user is already logged in, redirect appropriately
    if request.user.is_authenticated:
        # If student user, log them out and redirect to choose_portal
        if not (request.user.is_superuser or request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.is_admin)):
            logout(request)
            request.session.flush()
            messages.warning(request, 'Students cannot access the department admin portal. Please choose the correct portal below.')
            return redirect('choose_portal')
            return redirect('dept_admin:dashboard')

    # Generate CSRF token
    get_token(request)
    
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
                
                return redirect('dept_admin:dashboard')
            else:
                messages.error(request, 'Incorrect password.')
        except User.DoesNotExist:
            messages.error(request, 'User with this username does not exist.')
    
    # Generate new CSRF token for the form
    get_token(request)
    return render(request, 'dept_admin/login.html')

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
        # For General department, show all escalated tickets
        tickets = Ticket.objects.filter(
            department=department,
            status='escalated'
        ).select_related(
            'student',
            'original_department',
            'escalated_by'
        ).order_by('-escalated_at')
    else:
        # For other departments, show their own tickets
        tickets = Ticket.objects.filter(department=department)
    
    # Calculate statistics
    total_tickets = tickets.count()
    pending_count = tickets.filter(status='open').count()
    in_progress_count = tickets.filter(status='in_progress').count()
    resolved_count = tickets.filter(status='resolved').count()
    
    # Calculate SLA metrics
    total_resolved = tickets.filter(status='resolved')
    total_active = tickets.filter(status__in=['open', 'in_progress', 'on_hold'])
    
    # Calculate resolution rate
    resolution_rate = (resolved_count / total_tickets * 100) if total_tickets > 0 else 0
    
    # Calculate SLA compliance
    sla_compliant = tickets.filter(sla_breach=False).count()
    sla_compliance = (sla_compliant / total_tickets * 100) if total_tickets > 0 else 0
    
    # Calculate average response time
    tickets_with_response = tickets.exclude(first_response_at=None)
    total_response_time = timedelta()
    for ticket in tickets_with_response:
        total_response_time += ticket.first_response_at - ticket.created_at
    avg_response_hours = (total_response_time.total_seconds() / 3600) / tickets_with_response.count() if tickets_with_response.count() > 0 else 0
    
    # Get priority queue (tickets at risk of SLA breach) - only for non-General departments
    priority_queue = []
    if department.name != 'General':
        priority_queue = tickets.filter(
            status__in=['open', 'in_progress', 'on_hold'],
            sla_breach=False
        ).order_by('created_at')[:5]  # Show top 5 at-risk tickets
    
    context = {
        'department': department,
        'department_name': department_name,
        'tickets': tickets,
        'total_tickets': total_tickets,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'resolved_count': resolved_count,
        'resolution_rate': round(resolution_rate, 1),
        'sla_compliance': round(sla_compliance, 1),
        'avg_response_hours': round(avg_response_hours, 1),
        'priority_queue': priority_queue,
        'is_general_dept': department.name == 'General',  # Add this flag for template
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
                ticket.response = form.cleaned_data['response']
                if ticket.status == 'resolved':
                    ticket.resolved_at = timezone.now()
                ticket.save(update_fields=['status', 'response', 'resolved_at'])
            else:
                ticket = form.save(commit=False)
                if ticket.status == 'resolved':
                    ticket.resolved_at = timezone.now()
                ticket.save()

            # Create ticket update
            TicketUpdate.objects.create(
                ticket=ticket,
                user=request.user,
                comment=f"Status updated to {ticket.get_status_display()}",
                response=ticket.response
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

    complaints = Complaint.objects.filter(department=request.user.profile.department)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{request.user.profile.department}_complaints.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Ticket ID', 'Student', 'Description', 'Status', 'Created At'])
    
    for complaint in complaints:
        writer.writerow([
            complaint.ticket_id,
            complaint.user.username if complaint.user else 'Anonymous',
            complaint.description,
            complaint.status,
            complaint.created_at.strftime('%Y-%m-%d %H:%M:%S')
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
@user_passes_test(is_dept_admin)
def create_student(request):
    if request.method == 'POST':
        form = StudentCreationForm(request.POST)
        if form.is_valid():
            # Create user account
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            
            # Create student profile
            Profile.objects.create(
                user=user,
                department=request.user.profile.department,
                is_student=True
            )
            
            messages.success(request, f'Student account created successfully for {user.username}')
            return redirect('dept_admin:dashboard')
    else:
        form = StudentCreationForm()
    
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
        if 'excel_file' not in request.FILES:
            messages.error(request, 'Please upload an Excel file.')
            return render(request, 'dept_admin/bulk_create_students.html')
        
        try:
            created_students, errors = process_excel_file(
                request.FILES['excel_file'],
                request.user.profile.department
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
    
            return render(request, 'dept_admin/bulk_create_students.html', {
                'preview_data': created_students
            })
            
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
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
    
    # Get all escalated tickets in the General department
    tickets = Ticket.objects.filter(
        department__name='General',
        status='escalated'
    ).select_related(
        'student',
        'original_department',
        'escalated_by'
    ).order_by('-escalated_at')
    
    # Calculate statistics
    total_tickets = tickets.count()
    pending_tickets = tickets.filter(status='escalated').count()
    resolved_tickets = tickets.filter(status='resolved').count()
    
    context = {
        'tickets': tickets,
        'title': 'Escalated Tickets Management',
        'total_tickets': total_tickets,
        'pending_tickets': pending_tickets,
        'resolved_tickets': resolved_tickets,
    }
    
    return render(request, 'dept_admin/general_escalated_tickets.html', context)

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
