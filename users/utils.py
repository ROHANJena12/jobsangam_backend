# app/utils.py
import random
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    """
    Generates a 6-digit OTP as a string.
    """
    return str(random.randint(100000, 999999))

def send_verification_email(email, otp):
    """
    Sends a verification email containing the OTP to the specified email address.
    """
    subject = "Your Email Verification Code"
    message = f"Your verification code is {otp}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])