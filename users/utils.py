# # app/utils.py
# import random
# from django.core.mail import send_mail
# from django.conf import settings

# def generate_otp():
#     """
#     Generates a 6-digit OTP as a string.
#     """
#     return str(random.randint(100000, 999999))

# def send_verification_email(email, otp):
#     """
#     Sends a verification email containing the OTP to the specified email address.
#     """
#     subject = "Your Email Verification Code"
#     message = f"Your verification code is {otp}"
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

# app/utils.py
import random
from django.core.mail import send_mail
from django.conf import settings

def generate_otp() -> str:
    """
    Generate a 6-digit OTP as a string.
    Example: "483920"
    """
    return str(random.randint(100000, 999999))

def send_verification_email(email: str, otp: str, ttl_minutes: int = 2, use_async: bool = True):
    """
    Send a verification email with the OTP.
    
    By default this defers to Celery (async). If Celery is not running (e.g. in tests/dev),
    you can call with use_async=False to send immediately.
    """
    subject = "Your Email Verification Code"
    message = f"Your verification code is {otp}. It expires in {ttl_minutes} minutes."

    if use_async:
        from .tasks import send_verification_email_task
        send_verification_email_task.delay(email, otp, ttl_minutes)
    else:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
