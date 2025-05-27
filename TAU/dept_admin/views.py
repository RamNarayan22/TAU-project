from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from core.models import Complaint, AuditLog
from core.utils import send_status_notification
from .forms import UpdateComplaintForm
from datetime import datetime
from django.http import HttpResponse
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models import Complaint

@login_required
def dashboard(request):
    user = request.user
    dept = user.profile.department
    if not user.is_staff or not user.profile.is_admin:
        return redirect('student_dashboard')

    complaints = Complaint.objects.filter(department=dept)
    return render(request, 'department_dashboard.html', {'complaints': complaints, 'department': dept})

@login_required
def update_complaint(request, ticket_id):
    complaint = get_object_or_404(Complaint, ticket_id=ticket_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Complaint.STATUS_CHOICES).keys():
            complaint.status = status
            complaint.save()
            return redirect('department_dashboard')
    return render(request, 'dept_admin/update_complaint.html', {'complaint': complaint})

@login_required
def export_csv(request):
    dept = request.user.core_profile.department
    complaints = Complaint.objects.filter(department=dept)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="complaints.csv"'
    writer = csv.writer(response)
    writer.writerow(['Ticket ID', 'Description', 'Status', 'Created At', 'SLA Due'])
    for c in complaints:
        writer.writerow([c.ticket_id, c.description, c.status, c.created_at, c.sla_due])
    return response

from django.contrib.auth import authenticate, login
from django.contrib import messages

# from django.shortcuts import render, redirect
# from django.contrib.auth import authenticate, login
# from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if hasattr(user, 'core_profile') and user.is_staff and user.core_profile.department:
                return redirect('dashboard')  # Department admin dashboard
            else:
                return redirect('student_dashboard')  # Student dashboard
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'loginn.html')
