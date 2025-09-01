from django.urls import path
from .views import UserRegisterView
from .views import (
    UserRegisterView,
    RequestEmailVerificationView,
    VerifyEmailView,
    LoginView,
    ForgotPasswordRequestView,
    ResetPasswordView,
    CheckOldPasswordView,
)


urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("request-email-verification/", RequestEmailVerificationView.as_view(), name="request-email-verification"),
    path("login/", LoginView.as_view(), name="login"),
    path("forgot-password/", ForgotPasswordRequestView.as_view(), name="forgot_password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),
    path("check-old-password/", CheckOldPasswordView.as_view(), name="check-old-password"),
]
