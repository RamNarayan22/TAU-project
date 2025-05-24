from django.shortcuts import render


from Student.models import Complaint
from django.contrib.auth.decorators import login_required


def dept_dashboard(request):
    # You can also assign department from a user profile model if it's dynamic
    department = request.user.profile.department  # Assuming user has department set

    complaints = Complaint.objects.filter(department=department)
    
    context = {
        'department': department,
        'total_complaints': complaints.count(),
        'resolved_complaints': complaints.filter(status='Resolved').count(),
        'ongoing_complaints': complaints.filter(status__in=['Pending', 'In Progress']).count(),
        'recent_complaints': complaints.order_by('-created_at')[:5],
    }
    return render(request, 'Fadmin.html', context)

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_staff:
                dept = getattr(user.profile, 'department', None)
                if dept:
                    dept_slug = dept.lower().replace(" ", "")
                    return redirect(f'/admin/{dept_slug}/')
            return redirect('/')  # Redirect normal users somewhere
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')
