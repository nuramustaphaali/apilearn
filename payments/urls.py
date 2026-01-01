from django.urls import path
from .views import initiate_payment, verify_payment

urlpatterns = [
    path('initiate/<int:course_id>/', initiate_payment, name='payment-initiate'),
    path('verify/', verify_payment, name='payment-verify'),
]