from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from green_cart_api.users.models import Profile

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'date_of_birth', 'gender', 'phone_number', 'avatar',
            'newsletter_subscription', 'marketing_emails', 'bio', 'website'
        ]

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError(_("Passwords do not match."))
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user, _ = User.objects.create_user(**validated_data)
        profile, created = Profile.objects.get_or_create(user=user)
        return user

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'username', 'email',
            'is_active', 'is_admin', 'profile'
        ]
        read_only_fields = ['id', 'is_active', 'is_admin']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.save()

        profile = instance.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()
        return instance

class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=36, write_only=True)
    email = serializers.EmailField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        token = data.get('token')
        cached_token = cache.get(f'verification_token_{email}')
        if not cached_token or cached_token != token:
            raise serializers.ValidationError(_("Invalid or expired verification token."))
        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError(_("User not found."))
        if user.is_active:
            raise serializers.ValidationError(_("Email already verified."))
        return data

    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        user.is_active = True
        user.save()
        cache.delete(f'verification_token_{email}')
        return user

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'is_active', 'is_admin']