from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
        

from .forms import ComplaintForm

from .models import Complaint  # Assuming you have a Complaint model



# Create your views he
def register_view(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            return render(request, 'register.html', {'error': 'Passwords do not match'})

        if User.objects.filter(username=email).exists():
            return render(request, 'register.html', {'error': 'Email already registered'})

        user = User.objects.create_user(username=email, email=email, password=password)
        user.first_name = fullname
        user.save()

        return redirect('loginn')

    return render(request, 'register.html')


from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

def lp(request):
    if request.method == 'POST':
        email = request.POST.get('emaill')
        password = request.POST.get('passwordd') 
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('landingpage')
            else:
                messages.error(request, 'Incorrect password.')
        except User.DoesNotExist:
            messages.error(request, 'User with this email does not exist.')
    return render(request, 'login.html')

def logout(request):
    pass
 
from django.shortcuts import render, redirect
from core.models import Complaint, Department
from django.contrib.auth.decorators import login_required
from core.utils import generate_ticket_id, calculate_sla_due
from .forms import ComplaintForm

@login_required
def nt(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.ticket_id = generate_ticket_id(complaint.department.name)
            complaint.sla_due = calculate_sla_due()
            complaint.save()
            request.session['ticket_id'] = complaint.ticket_id
            return redirect('landingpage')
    else:
        form = ComplaintForm()
    return render(request, 'newticket.html', {'form': form})

@login_required
def landingpage(request):
    user = request.user

    # Pop ticket_id from session so it only shows once
    ticket_id = request.session.pop('ticket_id', None)

    total = Complaint.objects.filter(user=user).count()
    pending = Complaint.objects.filter(user=user, status='Pending').count()
    resolved = Complaint.objects.filter(user=user, status='Resolved').count()
    recent_complaints = Complaint.objects.filter(user=user).order_by('-created_at')[:3]

    return render(request, 'landingpage.html', {
        'student_name': user.first_name or user.username,
        'total': total,
        'pending': pending,
        'resolved': resolved,
        'recent_complaints': recent_complaints,
        'ticket_id': ticket_id,  # Make sure this is passed
    })
