# # users/tasks.py
# from celery import shared_task
# from django.core.mail import send_mail
# from django.conf import settings
# import smtplib

# @shared_task(
#     autoretry_for=(smtplib.SMTPException, ConnectionError, TimeoutError),
#     retry_backoff=True,   # 2^n seconds
#     retry_backoff_max=60, # cap at 60s
#     retry_jitter=True,    # add randomness
#     max_retries=3
# )

# def send_verification_email_task(email, otp, ttl_minutes=5):
#     subject = "Your Email Verification Code"
#     message = f"Your verification code is {otp}. It expires in {ttl_minutes} minutes."
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

# users/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import smtplib

@shared_task(
    autoretry_for=(smtplib.SMTPException, ConnectionError, TimeoutError),
    retry_backoff=True,    # exponential backoff: 2, 4, 8... seconds
    retry_backoff_max=60,  # max delay between retries = 60s
    retry_jitter=True,     # add randomness to avoid thundering herd
    max_retries=3
)
def send_verification_email_task(email: str, otp: str, ttl_minutes: int = 2):
    """
    Send verification OTP via email.
    Default validity is 2 minutes (consistent with backend policy).
    """
    subject = "Your Email Verification Code"
    message = f"Your verification code is {otp}. It expires in {ttl_minutes} minutes."
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False
    )
