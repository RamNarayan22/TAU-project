from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from core.models import Complaint, AuditLog, Profile
from datetime import datetime
from django.http import HttpResponse
import csv
from .forms import UpdateComplaintForm

def dept_admin_login(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.is_admin:
            return redirect('dept_admin:dashboard')
        return redirect('student:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and hasattr(user, 'profile') and user.profile.is_admin:
            login(request, user)
            return redirect('dept_admin:dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions')
    
    return render(request, 'dept_admin/login.html')

@login_required
def dept_admin_logout(request):
    logout(request)
    return redirect('dept_admin:login')

@login_required
def dashboard(request):
    if not request.user.profile.is_admin:
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
