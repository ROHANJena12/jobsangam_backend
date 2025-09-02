# from django.shortcuts import render
# from django.http import JsonResponse
# from .models import User, EmailVerification
# from .serializers import UserSerializer, EmailRequestSerializer, EmailVerifySerializer
# from rest_framework import generics, status
# from rest_framework.response import Response
# from rest_framework.exceptions import ValidationError
# from rest_framework.views import APIView
# from .utils import generate_otp, send_verification_email
# from .tasks import send_verification_email_task
# from .ratelimit import check_and_increment_email_otp_quota, increment_wrong_otp, reset_wrong_otp
# from django.utils import timezone
# import random
# from django.contrib.auth import authenticate
# from rest_framework.permissions import AllowAny
# from django.contrib.auth.hashers import check_password 


# def hello(request):
#     return JsonResponse({"message": "Backend is working!"})


# # class UserRegisterView(generics.CreateAPIView):
# #     queryset = User.objects.all()
# #     serializer_class = UserSerializer

# class UserRegisterView(generics.CreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#             user = serializer.save()
#             response_data = {
#                 "status": "success",
#                 "message": "User registered successfully",
#                 "data": serializer.data
#             }
#             return Response(response_data, status=status.HTTP_201_CREATED)
#         except ValidationError as e:
#             # Structure errors nicely
#             structured_errors = {k: v[0] if isinstance(v, list) else v for k, v in e.detail.items()}
#             response_data = {
#                 "status": "error",
#                 "message": "Validation failed",
#                 "data": structured_errors
#             }
#             return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        

# def generate_otp():
#     return str(random.randint(100000, 999999))


# class RequestEmailVerificationView(APIView):
#     def post(self, request):
#         serializer = EmailRequestSerializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#             email = serializer.validated_data["email"]

#             # ✅ Check if already registered
#             if User.objects.filter(email=email).exists():
#                 return Response({
#                     "status": "error",
#                     "message": "This email is already registered. Please login or use a different email.",
#                     "data": {"email": "Already registered"}
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             # ✅ Rate limit check: 3 per 15 min
#             allowed, remaining, ttl = check_and_increment_email_otp_quota(email)
#             if not allowed:
#                 return Response({
#                     "status": "error",
#                     "message": "Too many requests. Please try again later.",
#                     "data": {"retry_after_seconds": ttl}
#                 }, status=status.HTTP_429_TOO_MANY_REQUESTS)

#             otp = generate_otp()

#             # ✅ Create or update EmailVerification entry
#             obj, created = EmailVerification.objects.get_or_create(email=email, defaults={
#                 "otp": otp,
#                 "is_verified": False,
#                 "expires_at": timezone.now(),
#             })
#             obj.set_new_otp(otp, ttl_minutes=5)

#             # ✅ Send OTP async
#             send_verification_email_task.delay(email, otp)

#             return Response({
#                 "status": "success",
#                 "message": "OTP sent to email successfully",
#                 "data": {"email": email, "remaining_in_window": remaining}
#             }, status=status.HTTP_200_OK)

#         except ValidationError as e:
#             structured_errors = {k: (v[0] if isinstance(v, list) else v) for k, v in e.detail.items()}
#             return Response({
#                 "status": "error",
#                 "message": "Validation failed",
#                 "data": structured_errors
#             }, status=status.HTTP_400_BAD_REQUEST)



# class VerifyEmailView(APIView):
#     def post(self, request):
#         serializer = EmailVerifySerializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#             email = serializer.validated_data["email"]
#             otp = serializer.validated_data["otp"]

#             try:
#                 record = EmailVerification.objects.get(email=email)
#             except EmailVerification.DoesNotExist:
#                 return Response({
#                     "status": "error",
#                     "message": "Email not found",
#                     "data": {"email": "This email is not registered for verification"}
#                 }, status=status.HTTP_404_NOT_FOUND)

#             if record.is_expired():
#                 return Response({
#                     "status": "error",
#                     "message": "OTP expired",
#                     "data": {"otp": "The OTP has expired. Please request a new one."}
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             if record.otp != otp:
#                 # ⬇️ Count and rate limit wrong attempts
#                 count, remaining, ttl = increment_wrong_otp(email, window_seconds=900, max_fails=5)
#                 if remaining <= 0:
#                     return Response({
#                         "status": "error",
#                         "message": "Too many incorrect attempts. Please try again later.",
#                         "data": {"retry_after_seconds": ttl, "attempts": count}
#                     }, status=status.HTTP_429_TOO_MANY_REQUESTS)

#                 return Response({
#                     "status": "error",
#                     "message": "Invalid OTP",
#                     "data": {"otp": "The provided OTP is incorrect", "remaining_attempts": remaining}
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             # ✅ Success – mark verified and reset wrong-attempt counter
#             record.is_verified = True
#             record.save(update_fields=["is_verified"])
#             reset_wrong_otp(email)

#             return Response({
#                 "status": "success",
#                 "message": "Email verified successfully",
#                 "data": {"email": email}
#             }, status=status.HTTP_200_OK)

#         except ValidationError as e:
#             structured_errors = {k: (v[0] if isinstance(v, list) else v) for k, v in e.detail.items()}
#             return Response({
#                 "status": "error",
#                 "message": "Validation failed",
#                 "data": structured_errors
#             }, status=status.HTTP_400_BAD_REQUEST)
        
# class LoginView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         email = request.data.get("email")
#         password = request.data.get("password")

#         if not email or not password:
#             return Response({
#                 "status": "error",
#                 "message": "Email and password are required."
#             }, status=status.HTTP_400_BAD_REQUEST)

#         user = authenticate(request, email=email, password=password)
#         if user is not None:
#             # You can return tokens here if using JWT
#             return Response({
#                 "status": "success",
#                 "message": "Login successful",
#                 "data": {
#                     "user_id": user.id,
#                     "email": user.email,
#                     "role": user.role_type,
#                 }
#             }, status=status.HTTP_200_OK)
#         else:
#             return Response({
#                 "status": "error",
#                 "message": "Invalid email or password."
#             }, status=status.HTTP_401_UNAUTHORIZED)
        
# class ForgotPasswordRequestView(APIView):
#     def post(self, request):
#         email = request.data.get("email")
#         if not email:
#             return Response({
#                 "status": "error",
#                 "message": "Email is required."
#             }, status=status.HTTP_400_BAD_REQUEST)

#         if not User.objects.filter(email=email).exists():
#             return Response({
#                 "status": "error",
#                 "message": "No account found with this email."
#             }, status=status.HTTP_404_NOT_FOUND)

#         # Rate limiting
#         allowed, remaining, ttl = check_and_increment_email_otp_quota(email)
#         if not allowed:
#             return Response({
#                 "status": "error",
#                 "message": "Too many requests. Please try again later.",
#                 "data": {"retry_after_seconds": ttl}
#             }, status=status.HTTP_429_TOO_MANY_REQUESTS)

#         otp = generate_otp()
#         obj, created = EmailVerification.objects.get_or_create(email=email)
#         obj.set_new_otp(otp, ttl_minutes=5)

#         send_verification_email_task.delay(email, otp)

#         return Response({
#             "status": "success",
#             "message": "OTP sent to your email.",
#             "data": {"email": email}
#         })
    
# class ResetPasswordView(APIView):
#     def post(self, request):
#         email = request.data.get("email")
#         otp = request.data.get("otp")
#         new_password = request.data.get("new_password")

#         if not all([email, otp, new_password]):
#             return Response({
#                 "status": "error",
#                 "message": "Email, OTP, and new password are required."
#             }, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             record = EmailVerification.objects.get(email=email)
#         except EmailVerification.DoesNotExist:
#             return Response({
#                 "status": "error",
#                 "message": "Email not found for OTP verification."
#             }, status=status.HTTP_404_NOT_FOUND)

#         if record.is_expired() or record.otp != otp:
#             return Response({
#                 "status": "error",
#                 "message": "Invalid or expired OTP."
#             }, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             user = User.objects.get(email=email)
#             user.set_password(new_password)
#             user.save()

#             record.is_verified = True
#             record.save(update_fields=["is_verified"])
#             reset_wrong_otp(email)

#             return Response({
#                 "status": "success",
#                 "message": "Password reset successfully."
#             }, status=status.HTTP_200_OK)

#         except User.DoesNotExist:
#             return Response({
#                 "status": "error",
#                 "message": "User not found."
#             }, status=status.HTTP_404_NOT_FOUND)
        
# class CheckOldPasswordView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         email = request.data.get("email")
#         password = request.data.get("password")

#         if not email or not password:
#             return Response({
#                 "status": "error",
#                 "message": "Email and password are required."
#             }, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             user = User.objects.get(email=email)
#         except User.DoesNotExist:
#             return Response({
#                 "status": "error",
#                 "message": "User not found."
#             }, status=status.HTTP_404_NOT_FOUND)

#         is_same = check_password(password, user.password)

#         return Response({
#             "status": "success",
#             "message": "Password check completed.",
#             "data": {
#                 "is_same": is_same
#             }
#         })

from django.shortcuts import render
from django.http import JsonResponse
from .models import User, EmailVerification
from .serializers import UserSerializer, EmailRequestSerializer, EmailVerifySerializer
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from .tasks import send_verification_email_task
from .ratelimit import (
    check_and_increment_email_otp_quota,
    increment_wrong_otp,
    reset_wrong_otp,
    is_blocked,
    block_user,
    get_block_ttl,
)
from django.utils import timezone
import random
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from django.contrib.auth.hashers import check_password


def hello(request):
    return JsonResponse({"message": "Backend is working!"})


class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            response_data = {
                "status": "success",
                "message": "User registered successfully",
                "data": serializer.data,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            structured_errors = {
                k: v[0] if isinstance(v, list) else v for k, v in e.detail.items()
            }
            response_data = {
                "status": "error",
                "message": "Validation failed",
                "data": structured_errors,
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


def generate_otp():
    return str(random.randint(100000, 999999))


class RequestEmailVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailRequestSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data["email"]

            # ✅ Already registered?
            if User.objects.filter(email=email).exists():
                return Response(
                    {
                        "status": "error",
                        "message": "This email is already registered. Please login or use a different email.",
                        "data": {"email": "Already registered"},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ✅ Hard block check
            if is_blocked(email):
                return Response(
                    {
                        "status": "error",
                        "message": "Too many attempts. Please try again later.",
                        "data": {"retry_after_seconds": get_block_ttl(email)},
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            # ✅ Rate limit check (3 sends / 2 hours, 2 min cooldown)
            allowed, reason, ttl = check_and_increment_email_otp_quota(email)
            if not allowed:
                return Response(
                    {
                        "status": "error",
                        "message": "Too many OTP requests.",
                        "data": {"reason": reason, "retry_after_seconds": ttl},
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            otp = generate_otp()

            # ✅ Save OTP to DB
            obj, created = EmailVerification.objects.get_or_create(
                email=email,
                defaults={
                    "otp": otp,
                    "is_verified": False,
                    "expires_at": timezone.now(),
                },
            )
            obj.set_new_otp(otp, ttl_minutes=2)  # OTP valid for 2 minutes

            # ✅ Send OTP async
            send_verification_email_task.delay(email, otp)

            return Response(
                {
                    "status": "success",
                    "message": "OTP sent successfully.",
                    "data": {"email": email, "valid_for": 120, "cooldown": 120},
                },
                status=status.HTTP_200_OK,
            )

        except ValidationError as e:
            structured_errors = {
                k: (v[0] if isinstance(v, list) else v) for k, v in e.detail.items()
            }
            return Response(
                {
                    "status": "error",
                    "message": "Validation failed",
                    "data": structured_errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerifySerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data["email"]
            otp = serializer.validated_data["otp"]

            # ✅ Hard block?
            if is_blocked(email):
                return Response(
                    {
                        "status": "error",
                        "message": "Too many attempts. Please try again later.",
                        "data": {"retry_after_seconds": get_block_ttl(email)},
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            try:
                record = EmailVerification.objects.get(email=email)
            except EmailVerification.DoesNotExist:
                return Response(
                    {
                        "status": "error",
                        "message": "Email not found",
                        "data": {
                            "email": "This email is not registered for verification"
                        },
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            if record.is_expired():
                return Response(
                    {
                        "status": "error",
                        "message": "OTP expired",
                        "data": {
                            "otp": "The OTP has expired. Please request a new one."
                        },
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if record.otp != otp:
                # ⬇️ Wrong OTP attempts (max 3 → block 2h)
                count, remaining, ttl = increment_wrong_otp(
                    email, window_seconds=7200, max_fails=3
                )
                if remaining <= 0:
                    block_user(email)
                    return Response(
                        {
                            "status": "error",
                            "message": "Too many incorrect attempts. Try again later.",
                            "data": {"retry_after_seconds": ttl, "attempts": count},
                        },
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )

                return Response(
                    {
                        "status": "error",
                        "message": "Invalid OTP",
                        "data": {
                            "otp": "The provided OTP is incorrect",
                            "remaining_attempts": remaining,
                        },
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ✅ Success – mark verified and reset wrong-attempt counter
            record.is_verified = True
            record.save(update_fields=["is_verified"])
            reset_wrong_otp(email)

            return Response(
                {
                    "status": "success",
                    "message": "Email verified successfully",
                    "data": {"email": email},
                },
                status=status.HTTP_200_OK,
            )

        except ValidationError as e:
            structured_errors = {
                k: (v[0] if isinstance(v, list) else v) for k, v in e.detail.items()
            }
            return Response(
                {
                    "status": "error",
                    "message": "Validation failed",
                    "data": structured_errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


# (Login, ForgotPassword, ResetPassword, CheckOldPassword stay same)
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {
                    "status": "error",
                    "message": "Email and password are required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, email=email, password=password)
        if user is not None:
            return Response(
                {
                    "status": "success",
                    "message": "Login successful",
                    "data": {
                        "user_id": user.id,
                        "email": user.email,
                        "role": user.role_type,
                    },
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"status": "error", "message": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class ForgotPasswordRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"status": "error", "message": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not User.objects.filter(email=email).exists():
            return Response(
                {"status": "error", "message": "No account found with this email."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if is_blocked(email):
            return Response(
                {
                    "status": "error",
                    "message": "Too many attempts. Try again later.",
                    "data": {"retry_after_seconds": get_block_ttl(email)},
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        allowed, reason, ttl = check_and_increment_email_otp_quota(email)
        if not allowed:
            return Response(
                {
                    "status": "error",
                    "message": "Too many requests.",
                    "data": {"reason": reason, "retry_after_seconds": ttl},
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        otp = generate_otp()
        obj, created = EmailVerification.objects.get_or_create(email=email)
        obj.set_new_otp(otp, ttl_minutes=2)
        send_verification_email_task.delay(email, otp)

        return Response(
            {
                "status": "success",
                "message": "OTP sent to your email.",
                "data": {"email": email, "valid_for": 120},
            }
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")

        if not all([email, otp, new_password]):
            return Response(
                {
                    "status": "error",
                    "message": "Email, OTP, and new password are required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            record = EmailVerification.objects.get(email=email)
        except EmailVerification.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": "Email not found for OTP verification.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if record.is_expired() or record.otp != otp:
            return Response(
                {"status": "error", "message": "Invalid or expired OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            record.is_verified = True
            record.save(update_fields=["is_verified"])
            reset_wrong_otp(email)

            return Response(
                {"status": "success", "message": "Password reset successfully."},
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {"status": "error", "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class CheckOldPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {
                    "status": "error",
                    "message": "Email and password are required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"status": "error", "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_same = check_password(password, user.password)

        return Response(
            {
                "status": "success",
                "message": "Password check completed.",
                "data": {"is_same": is_same},
            }
        )
