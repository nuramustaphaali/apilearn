from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.urls import reverse

# Models
from .models import Payment
from courses.models import Course, Enrollment
from .paystack import Paystack

# Emails
from django.core.mail import send_mail

@login_required
def initiate_payment(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    
    # 1. Check if already enrolled
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.info(request, "You are already enrolled!")
        return redirect('course-detail', pk=course.id)

    # ----------------------------------------
    # 2. LOGIC FOR FREE COURSES (Price == 0)
    # ----------------------------------------
    if course.price == 0:
        # A. Create Enrollment Immediately
        Enrollment.objects.get_or_create(student=request.user, course=course)
        
        # B. Record a "Success" payment of 0.00 for history tracking
        Payment.objects.create(
            user=request.user,
            course=course,
            amount=0,
            reference=get_random_string(12).upper(), # Internal Reference
            status=Payment.SUCCESS
        )

        # C. Send Success Message & Redirect to Course
        messages.success(request, f"Successfully enrolled in {course.title}!")
        return redirect('course-detail', pk=course.id)


    # ----------------------------------------
    # 3. LOGIC FOR PAID COURSES (Paystack)
    # ----------------------------------------
    
    # Generate unique reference
    ref = get_random_string(12).upper()
    
    # Create Pending Payment Record
    payment = Payment.objects.create(
        user=request.user,
        course=course,
        amount=course.price,
        reference=ref,
        status=Payment.PENDING
    )

    # Call Paystack API
    paystack = Paystack()
    callback_url = request.build_absolute_uri(reverse('payment-verify'))
    
    response = paystack.initialize_transaction(
        email=request.user.email,
        amount=course.price,
        reference=ref,
        callback_url=callback_url
    )

    if response['status']:
        return redirect(response['data']['authorization_url'])
    else:
        messages.error(request, "Payment initialization failed.")
        return redirect('course-list')


def verify_payment(request):
    ref = request.GET.get('reference')
    
    if not ref:
        return redirect('course-list')

    payment = get_object_or_404(Payment, reference=ref)
    
    paystack = Paystack()
    response = paystack.verify_transaction(ref)

    if response['status'] and response['data']['status'] == 'success':
        # 1. Update Payment Status
        payment.status = Payment.SUCCESS
        payment.save()
        
        # 2. Create Enrollment
        Enrollment.objects.get_or_create(student=payment.user, course=payment.course)
        
        # 3. Send Email
        send_mail(
            subject=f"Payment Receipt: {payment.course.title}",
            message=f"Payment Received: ${payment.amount}\nReference: {payment.reference}\n\nAccess your course now!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.user.email],
            fail_silently=True
        )

        # Make sure this template exists: templates/payments/payment_success.html
        return render(request, 'payments/payment_success.html', {'payment': payment, 'course': payment.course})
    
    else:
        payment.status = Payment.FAILED
        payment.save()
        
        # Make sure this template exists: templates/payments/payment_failed.html
        return render(request, 'payments/payment_failed.html', {'payment': payment, 'course': payment.course})