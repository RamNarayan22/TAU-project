from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from core.models import Complaint, AuditLog, DepartmentProfile
from core.utils import send_status_notification
from .forms import UpdateComplaintForm
import csv
from django.http import HttpResponse
from datetime import datetime

from .models import Complaint


@login_required
def dashboard_view(request):
    dept = request.user.core_profile.department
    complaints = Complaint.objects.filter(department=dept)
    status_filter = request.GET.get('status')
    if status_filter:
        complaints = complaints.filter(status=status_filter)

    overdue = complaints.filter(status__in=['Open', 'In Progress'], sla_due__lt=datetime.now())
    stats = {s: complaints.filter(status=s).count() for s in dict(Complaint.STATUS_CHOICES)}

    return render(request, 'depatment_dashboard.html', {
        'complaints': complaints,
        'complaint_counts': stats,
        'overdue': overdue
    })

@login_required
def update_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if request.method == 'POST':
        form = UpdateComplaintForm(request.POST, instance=complaint)
        if form.is_valid():
            prev_status = complaint.status
            form.save()
            send_status_notification(complaint)
            AuditLog.objects.create(
                complaint=complaint,
                user=request.user,
                action=f"Updated from {prev_status} to {complaint.status}"
            )
            return redirect('dashboard')
    else:
        form = UpdateComplaintForm(instance=complaint)
    return render(request,'update_complaint.html', {'form': form})

@login_required
def export_csv(request):
    dept = request.user.core_profile.department
    complaints = Complaint.objects.filter(department=dept)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="complaints.csv"'
    writer = csv.writer(response)
    writer.writerow(['Ticket ID', 'Title', 'Status', 'Created At', 'SLA Due'])
    for c in complaints:
        writer.writerow([c.ticket_id, c.title, c.status, c.created_at, c.sla_due])
    return response

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)

            # Check if this is a department admin (faculty)
            if hasattr(user, 'core_profile') and user.is_staff:
                return redirect('dashboard')  # Department admin dashboard

            # Else assume student
            return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'loginn.html')

