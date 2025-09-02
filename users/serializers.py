# from rest_framework import serializers
# from .models import User, EmailVerification


# class UserSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True)

#     class Meta:
#         model = User
#         fields = ['id', 'full_name', 'email', 'password', 'mobile', 'work_status', 'role_type']

#     def create(self, validated_data):
#         password = validated_data.pop('password')
#         user = User(**validated_data)
#         user.set_password(password)  # hash password
#         user.save()
#         return user

# class EmailRequestSerializer(serializers.Serializer):
#     email = serializers.EmailField()

# class EmailVerifySerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     otp = serializers.CharField(max_length=6)

from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'email',
            'password',
            'mobile',
            'work_status',
            'role_type',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # hash password
        user.save()
        return user


class EmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        """Normalize and validate email."""
        return value.strip().lower()


class EmailVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate_email(self, value):
        """Normalize email before passing downstream."""
        return value.strip().lower()

    def validate_otp(self, value):
        """Ensure OTP is exactly 6 numeric digits."""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value
