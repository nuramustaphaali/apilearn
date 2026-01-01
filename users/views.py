from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import default_token_generator
from .forms import UserRegistrationForm
from django.contrib.auth.decorators import login_required


User = get_user_model()

def register(request):
    if request.user.is_authenticated:
        return redirect('course-list')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # 1. Create user but DO NOT save to DB yet (to set is_active=False)
            user = form.save(commit=False)
            user.is_active = False # Deactivate until email verified
            user.save()

            # 2. Prepare Email Data
            current_site = get_current_site(request)
            mail_subject = 'Activate your ApiLearn Account'
            
            # Render the email body from a template
            message = render_to_string('users/activation_email_body.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
                'protocol': 'https' if request.is_secure() else 'http'
            })

            # 3. Send Email
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.content_subtype = "html" # Main content is text/html
            email.send()

            # 4. Redirect to "Check Email" page
            return render(request, 'users/email_sent.html')
            
        else:
            messages.error(request, "Registration failed. Please check the errors below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


def activate_account(request, uidb64, token):
    """
    Handles the click from the email link.
    """
    try:
        # Decode the User ID
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        print(f"❌ Activation Error: User lookup failed. Error: {e}")
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        # SUCCESS
        user.is_active = True
        user.save()
        login(request, user) # Optional: Log them in instantly
        return render(request, 'users/activation_result.html', {'success': True})
    else:
        # FAILURE - Debugging Info
        print(f"❌ Activation Failed!")
        if user is None:
            print(f"   Reason: User not found for ID {uidb64}")
        else:
            print(f"   Reason: Invalid Token for user {user.username}")
        
        return render(request, 'users/activation_result.html', {'success': False})


from django.db.models import Sum, Count
from courses.models import Course, Enrollment, Certificate
from payments.models import Payment

@login_required
def dashboard(request):
    """Redirects user to the correct dashboard based on role."""
    if request.user.role == 'instructor':
        return redirect('instructor-dashboard')
    elif request.user.role == 'student':
        return redirect('student-dashboard')
    return redirect('course-list') # Admin or other fallback

@login_required
def student_dashboard(request):
    # 1. Get My Courses
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    
    # 2. Get My Certificates
    certificates = Certificate.objects.filter(student=request.user)
    
    context = {
        'enrollments': enrollments,
        'certificates': certificates
    }
    return render(request, 'dashboard/student_dashboard.html', context)

@login_required
def instructor_dashboard(request):
    # Security: Ensure only instructors can see this
    if request.user.role != 'instructor':
        return redirect('student-dashboard')

    # 1. Get My Courses
    courses = Course.objects.filter(instructor=request.user)
    
    # 2. Calculate Stats
    total_students = Enrollment.objects.filter(course__instructor=request.user).count()
    total_courses = courses.count()
    
    # Calculate Earnings (Sum of successful payments for my courses)
    earnings_data = Payment.objects.filter(
        course__instructor=request.user, 
        status='success'
    ).aggregate(Sum('amount'))
    
    total_earnings = earnings_data['amount__sum'] or 0

    context = {
        'courses': courses,
        'total_students': total_students,
        'total_courses': total_courses,
        'total_earnings': total_earnings,
    }
    return render(request, 'dashboard/instructor_dashboard.html', context)

# users/views.py
from .forms import ProfileUpdateForm

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            # Save Profile Data (Avatar/Bio)
            form.save()
            
            # Save User Data (Full Name)
            user = request.user
            user.full_name = form.cleaned_data.get('full_name')
            user.save()
            
            messages.success(request, "Profile updated successfully!")
            return redirect('dashboard')
    else:
        # Pre-fill form
        form = ProfileUpdateForm(instance=request.user.profile, initial={'full_name': request.user.full_name})
    
    return render(request, 'users/edit_profile.html', {'form': form})