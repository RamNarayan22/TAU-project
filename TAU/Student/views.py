from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.middleware.csrf import get_token
from django.db import transaction

from .forms import ComplaintForm, StudentRegistrationForm
from core.models import Complaint, Profile, Department



# Create your views he
@csrf_exempt  # Temporarily disable CSRF to test form submission
def register_view(request):
    print("\nDEBUG: -------- Registration Request --------")
    print(f"DEBUG: Request Method: {request.method}")
    
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        print("\nDEBUG: -------- Form Data --------")
        print(f"DEBUG: Form is bound: {form.is_bound}")
        print(f"DEBUG: Raw POST data: {dict(request.POST)}")
        
        # Debug password fields specifically
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        print(f"DEBUG: password1 length: {len(password1)}")
        print(f"DEBUG: password2 length: {len(password2)}")
        
        if form.is_valid():
            print("\nDEBUG: Form is valid")
            try:
                with transaction.atomic():
                    # Create the user
                    user = form.save()
                    print(f"DEBUG: User created successfully: {user.email}")
                    
                    # Create user profile with default department
                    default_dept, _ = Department.objects.get_or_create(name='Others')
                    profile = Profile(user=user, department=default_dept)
                    profile.save()
                    print("DEBUG: Profile created successfully")
                    
                    messages.success(request, 'Registration successful! Please login with your email and password.')
                    return redirect('student:loginn')
            except Exception as e:
                print(f"DEBUG: Error during registration: {str(e)}")
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            print("\nDEBUG: -------- Form Errors --------")
            print(f"DEBUG: Form errors: {form.errors}")
            print(f"DEBUG: Non-field errors: {form.non_field_errors()}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
                    print(f"DEBUG: Field '{field}' error: {error}")
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'register.html', {'form': form})


from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

@ensure_csrf_cookie
def lp(request):
    # If user is already logged in, redirect appropriately
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect('dept_admin:dashboard')
        return redirect('student:landingpage')

    # Generate CSRF token
    get_token(request)
    
    if request.method == 'POST':
        email = request.POST.get('emaill')
        password = request.POST.get('passwordd') 
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                # Check if user is trying to access student portal as admin
                if user.is_superuser or user.is_staff:
                    messages.error(request, 'Please use the department admin login page.')
                    return redirect('dept_admin:login')
                
                login(request, user)
                # Ensure session is saved
                request.session.save()
                return redirect('student:landingpage')
            else:
                messages.error(request, 'Incorrect password.')
        except User.DoesNotExist:
            messages.error(request, 'User with this email does not exist.')
    return render(request, 'login.html')

def logout_view(request):
    auth_logout(request)
    messages.success(request, 'You have been successfully logged out.')
    # Clear any remaining session data
    request.session.flush()
    return redirect('student:loginn')

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
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()
            
            # Store ticket ID in session and show success message
            request.session['ticket_id'] = complaint.ticket_id
            messages.success(request, f'Complaint submitted successfully! Ticket ID: {complaint.ticket_id}')
            
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

def student_root(request):
    """
    Root view for student app - handles redirection based on user type
    """
    # For authenticated users
    if request.user.is_authenticated:
        # If admin user, show warning and redirect to student login
        if request.user.is_superuser or request.user.is_staff:
            auth_logout(request)  # Log them out from admin account
            messages.warning(request, 'Please use a student account to access the student portal.')
            return redirect('student:loginn')
        # If student user, go to landing page
        return redirect('student:landingpage')
    # For unauthenticated users, go to student login
    return redirect('student:loginn')
