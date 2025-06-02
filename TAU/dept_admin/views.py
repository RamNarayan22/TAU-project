from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from core.models import Complaint, AuditLog, Profile
from datetime import datetime
from django.http import HttpResponse
import csv
from .forms import UpdateComplaintForm
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.middleware.csrf import rotate_token, get_token

@ensure_csrf_cookie
@csrf_protect
def dept_admin_login(request):
    # If user is logged in as a regular student, keep them there
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and not request.user.profile.is_admin:
            return redirect('student:landingpage')
        # If admin user, proceed to dashboard
        elif hasattr(request.user, 'profile') and request.user.profile.is_admin:
            return redirect('dept_admin:dashboard')
        # If no profile, log them out
        logout(request)
    
    # If this is a login attempt
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_active:
            # Strict check for admin privileges
            if hasattr(user, 'profile') and user.profile.is_admin:
                login(request, user)
                rotate_token(request)
                request.session.save()
                return redirect('dept_admin:dashboard')
            else:
                # If regular student, redirect to student login
                messages.info(request, 'Please use the student login page.')
                return redirect('student:loginn')
        else:
            messages.error(request, 'Invalid credentials')
    
    # Generate new CSRF token for the form
    get_token(request)
    return render(request, 'dept_admin/login.html')

@login_required
def dept_admin_logout(request):
    if request.method == 'POST':
        is_admin = hasattr(request.user, 'profile') and request.user.profile.is_admin
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        # Redirect admins to admin login, students to student login
        if is_admin:
            return redirect('dept_admin:login')
        return redirect('student:loginn')
    return redirect('student:loginn')  # Default to student login

@login_required
def dashboard(request):
    # Strict check for admin privileges
    if not hasattr(request.user, 'profile') or not request.user.profile.is_admin:
        logout(request)  # Ensure user is logged out
        messages.error(request, 'Access denied. Department admin privileges required.')
        return redirect('dept_admin:login')
    
    complaints = Complaint.objects.filter(department=request.user.profile.department)
    
    # Get counts for different statuses
    pending_count = complaints.filter(status='Pending').count()
    in_progress_count = complaints.filter(status='In Progress').count()
    resolved_count = complaints.filter(status='Resolved').count()
    
    context = {
        'complaints': complaints,
        'department': request.user.profile.department,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'resolved_count': resolved_count
    }
    return render(request, 'dept_admin/dashboard.html', context)

@login_required
def update_complaint(request, complaint_id):
    if not request.user.profile.is_admin:
        messages.error(request, 'Access denied. Department admin privileges required.')
        return redirect('dept_admin:login')

    complaint = get_object_or_404(Complaint, id=complaint_id, department=request.user.profile.department)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Complaint.STATUS_CHOICES):
            old_status = complaint.status
            complaint.status = new_status
            complaint.save()
            
            # Create audit log
            AuditLog.objects.create(
                complaint=complaint,
                performed_by=request.user,
                action=f'Status changed from {old_status} to {new_status}'
            )
            
            messages.success(request, 'Complaint status updated successfully')
            return redirect('dept_admin:dashboard')
    
    return render(request, 'dept_admin/update_complaint.html', {'complaint': complaint})

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
