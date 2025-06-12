from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.middleware.csrf import get_token, rotate_token
from django.db import transaction
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from .forms import ComplaintForm, StudentRegistrationForm
from core.models import Profile, Department
from .models import Ticket, SLABreachLog
from .decorators import student_required



# Create your views he


from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

@ensure_csrf_cookie
def lp(request):
    # If user is already logged in, redirect appropriately
    if request.user.is_authenticated:
        # Ensure profile exists
        if not hasattr(request.user, 'profile'):
            from core.models import Profile
            Profile.objects.create(user=request.user, is_admin=request.user.is_staff)
        # If admin user, log them out and redirect to choose_portal
        if request.user.is_superuser or request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.is_admin):
            auth_logout(request)
            request.session.flush()
            messages.warning(request, 'Department admins cannot access the student portal. Please choose the correct portal below.')
            return redirect('choose_portal')
        # Check if password change is required
        if request.user.profile.must_change_password:
            return redirect('student:change_password')
        return redirect('student:landingpage')

    # Generate CSRF token
    get_token(request)
    
    if request.method == 'POST':
        email = request.POST.get('emaill')
        password = request.POST.get('passwordd') 
        try:
            user_obj = User.objects.get(email=email)
            # Check if user is a department admin before authentication
            if hasattr(user_obj, 'profile') and user_obj.profile.is_admin:
                messages.error(request, 'Department admins cannot login to the student portal. Please use the department admin login page.')
                return redirect('dept_admin:login')
                
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                # Double check that this is not an admin user
                if user.is_superuser or user.is_staff or (hasattr(user, 'profile') and user.profile.is_admin):
                    messages.error(request, 'Department admins cannot login to the student portal. Please use the department admin login page.')
                    return redirect('dept_admin:login')
                
                login(request, user)
                # Rotate CSRF token on login
                rotate_token(request)
                # Ensure session is saved
                request.session.save()
                
                # Check if password change is required
                if user.profile.must_change_password:
                    messages.info(request, 'Please change your password to continue.')
                    return redirect('student:change_password')
                    
                return redirect('student:landingpage')
            else:
                messages.error(request, 'Incorrect password.')
        except User.DoesNotExist:
            messages.error(request, 'User with this email does not exist.')
    
    # Generate new CSRF token for the form
    get_token(request)
    return render(request, 'login.html')

def logout_view(request):
    auth_logout(request)
    request.session.flush()
    messages.success(request, 'You have been successfully logged out.')
    return redirect('student:loginn')

@login_required
def change_password(request):
    # Ensure profile exists
    if not hasattr(request.user, 'profile'):
        from core.models import Profile
        Profile.objects.create(user=request.user, is_admin=request.user.is_staff)
    if not request.user.profile.must_change_password:
        return redirect('student:landingpage')

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            
            profile = request.user.profile
            profile.must_change_password = False
            profile.save()

            messages.success(request, 'Your password was successfully updated!')
            return redirect('student:landingpage')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})

from django.shortcuts import render, redirect
from core.models import Complaint, Department
from django.contrib.auth.decorators import login_required
from core.utils import generate_ticket_id, calculate_sla_due
from .forms import ComplaintForm

@login_required
def nt(request):
    # Check if user is a superuser or staff member
    if request.user.is_superuser or request.user.is_staff:
        messages.error(request, 'Admin users cannot submit complaints. Please use a student account.')
        return redirect('student:loginn')

    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to submit a complaint.')
        return redirect('student:loginn')

    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a Ticket instead of a Complaint
            ticket = Ticket(
                student=request.user,
                department=form.cleaned_data['department'],
                subject=form.cleaned_data['subject'],
                description=form.cleaned_data['description'],
                priority=form.cleaned_data.get('priority', 'medium'),
                status='open'
            )
            ticket.save()
            
            # Store ticket ID in session and show success message
            request.session['ticket_id'] = ticket.ticket_id
            messages.success(request, f'Complaint submitted successfully! Ticket ID: {ticket.ticket_id}')
            
            # Ensure user session is maintained
            request.session.save()
            
            # Redirect to student landing page
            return redirect('student:landingpage')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ComplaintForm()
    
    context = {
        'form': form,
        'student_name': request.user.first_name or request.user.username
    }
    return render(request, 'newticket.html', context)

@login_required
@student_required
def landingpage(request):
    user = request.user

    # Pop ticket_id from session so it only shows once
    ticket_id = request.session.pop('ticket_id', None)

    total = Ticket.objects.filter(student=user).count()
    pending = Ticket.objects.filter(student=user, status__in=['open', 'in_progress']).count()
    resolved = Ticket.objects.filter(student=user, status='resolved').count()
    recent_tickets = Ticket.objects.filter(student=user).order_by('-created_at')[:3]

    return render(request, 'landingpage.html', {
        'student_name': user.first_name or user.username,
        'total': total,
        'pending': pending,
        'resolved': resolved,
        'recent_complaints': recent_tickets,
        'ticket_id': ticket_id,
    })

def student_root(request):
    """
    Root view for student app - handles redirection based on user type
    """
    # For authenticated users
    if request.user.is_authenticated:
        # If admin user, show warning and redirect to admin login
        if request.user.is_superuser or request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.is_admin):
            auth_logout(request)  # Log them out from admin account
            messages.warning(request, 'Department admins cannot access the student portal. Please use the department admin login page.')
            return redirect('dept_admin:login')
        # If student user, go to landing page
        return redirect('student:landingpage')
    # For unauthenticated users, go to student login
    return redirect('student:loginn')

@login_required
def sla_dashboard(request):
    # Get date range (default: last 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Overall metrics
    total_tickets = Complaint.objects.filter(created_at__gte=start_date).count()
    resolved_tickets = Complaint.objects.filter(
        created_at__gte=start_date,
        status='Resolved'
    ).count()
    
    # Calculate resolution rate
    resolution_rate = (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0
    
    # Calculate average resolution time
    avg_resolution_time = Complaint.objects.filter(
        created_at__gte=start_date,
        status='Resolved'
    ).aggregate(
        avg_time=Avg(
            'updated_at' - 'created_at'
        )
    )['avg_time']
    
    if avg_resolution_time:
        avg_resolution_hours = avg_resolution_time.total_seconds() / 3600
    else:
        avg_resolution_hours = 0
    
    # Department-wise metrics
    departments = Department.objects.all()
    department_metrics = []
    
    for dept in departments:
        dept_tickets = Complaint.objects.filter(
            department=dept,
            created_at__gte=start_date
        )
        
        dept_total = dept_tickets.count()
        if dept_total > 0:
            dept_resolved = dept_tickets.filter(status='Resolved').count()
            
            department_metrics.append({
                'name': dept.name,
                'total_tickets': dept_total,
                'resolution_rate': (dept_resolved / dept_total * 100),
            })
    
    context = {
        'total_tickets': total_tickets,
        'resolution_rate': resolution_rate,
        'avg_resolution_hours': avg_resolution_hours,
        'department_metrics': department_metrics,
        'days': days
    }
    
    return render(request, 'Student/sla_dashboard.html', context)

@login_required
def vt(request):
    """View all tickets for the current user."""
    user = request.user
    
    # Get filter parameters
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    
    # Base queryset
    tickets = Complaint.objects.filter(user=user).order_by('-created_at')
    
    # Apply filters
    if status:
        tickets = tickets.filter(status=status)
    if priority:
        tickets = tickets.filter(priority=priority)
    
    context = {
        'tickets': tickets,
        'current_status': status,
        'current_priority': priority,
        'status_choices': Complaint.STATUS_CHOICES,
        'priority_choices': Complaint.PRIORITY_CHOICES,
    }
    return render(request, 'viewtickets.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user has a profile
            try:
                profile = user.profile
                # Check user role and redirect accordingly
                if profile.role == 'student':
                    if request.path.startswith('/department/'):
                        messages.error(request, 'Students cannot access department dashboard.')
                        return redirect('student:loginn')
                    login(request, user)
                    if profile.must_change_password:
                        return redirect('student:change_password')
                    return redirect('student:landingpage')
                
                elif profile.role == 'dept_admin':
                    if not request.path.startswith('/department/'):
                        messages.error(request, 'Department admins must use the department login page.')
                        return redirect('dept_admin:login')
                    login(request, user)
                    if profile.must_change_password:
                        return redirect('dept_admin:change_password')
                    return redirect('dept_admin:dashboard')
                
                elif profile.role == 'superuser':
                    login(request, user)
                    if profile.must_change_password:
                        return redirect('core:change_password')
                    return redirect('core:dashboard')
                
            except Exception as e:
                messages.error(request, 'Invalid login credentials or missing profile.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

@login_required
@student_required
def new_ticket(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.student = request.user
            ticket.save()
            messages.success(request, 'Ticket submitted successfully!')
            return redirect('student:landingpage')
    else:
        form = ComplaintForm()
        # Set department queryset to show only unique departments
        form.fields['department'].queryset = Department.objects.all().order_by('name')
    
    return render(request, 'newticket.html', {'form': form})

@login_required
@student_required
def view_tickets(request):
    tickets = Ticket.objects.filter(student=request.user).order_by('-created_at')
    context = {
        'tickets': tickets
    }
    return render(request, 'viewtickets.html', context)
