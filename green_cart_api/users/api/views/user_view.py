import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.contrib.auth import get_user_model

from green_cart_api.users.models import Profile
from ..serializers.user_serializer import (
    UserRegistrationSerializer, UserSerializer, EmailVerificationSerializer, UserListSerializer
)
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.db import transaction
from green_cart_api.global_data.email import EmailUtil
from django.conf import settings
from django.core.cache import cache
from urllib.parse import urlencode

User = get_user_model()
logger = logging.getLogger(__name__)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register a new user",
        description="Creates a new user account and sends a verification link to the provided email. The user is inactive until the email is verified by clicking the link. The process is atomic; if any step (validation, user creation, profile creation, or email sending) fails, no changes are saved.",
        request=UserRegistrationSerializer,
        responses={
            201: OpenApiResponse(
                response=UserSerializer,
                description="User created successfully",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={
                            "user": {
                                "id": 1,
                                "first_name": "John",
                                "last_name": "Doe",
                                "username": "johndoe",
                                "email": "john.doe@example.com",
                                "is_active": False,
                                "is_admin": False,
                                "profile": {
                                    "date_of_birth": None,
                                    "gender": None,
                                    "phone_number": None,
                                    "avatar": None,
                                    "newsletter_subscription": True,
                                    "marketing_emails": True,
                                    "bio": None,
                                    "website": None
                                }
                            },
                            "message": "User created successfully. Please check your email for the verification link."
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid input data or email sending failed")
        }
    )
    def post(self, request):
        logger.info("Received registration request for email: %s", request.data.get('email'))
        serializer = UserRegistrationSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.error("Validation failed for registration: %s", str(e))
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data.copy()
        validated_data.pop('confirm_password', None)

        try:
            with transaction.atomic():
                # Create user and get verification token
                user, verification_token = User.objects.create_user(**validated_data)

                # Create profile
                Profile.objects.get_or_create(user=user)

                # Generate verification link
                base_url = request.build_absolute_uri('/api/verify_email/')
                query_params = urlencode({'token': verification_token, 'email': user.email})
                verification_link = f"{base_url}?{query_params}"

                # Send verification email
                email_util = EmailUtil(prod=not settings.DEBUG)
                context = {
                    'first_name': user.first_name,
                    'verification_link': verification_link,
                    'site_name': 'Green Cart'
                }
                logger.info("Sending verification email to: %s", user.email)
                email_sent = email_util.send_email_with_template(
                    template='emails/verification_email.html',
                    context=context,
                    receivers=[user.email],
                    subject=_('Verify Your Green Cart Account')
                )

                if not email_sent:
                    logger.error("Failed to send verification email to: %s", user.email)
                    raise ValueError(_("Failed to send verification email"))

                # Store token in cache
                cache.set(f'verification_token_{user.email}', verification_token, timeout=24*60*60)
                logger.info("Verification token stored in cache for: %s", user.email)

                logger.info("User registered successfully: %s", user.email)
                return Response({
                    'user': UserSerializer(user, context={'request': request}).data,
                    'message': _('User created successfully. Please check your email for the verification link.')
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error("Registration failed: %s", str(e))
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(TokenObtainPairView):
    @extend_schema(
        summary="Login to obtain JWT tokens",
        description="Authenticates a user and returns JWT access and refresh tokens. The user must have a verified email (is_active=True).",
        responses={
            200: OpenApiResponse(
                description="Tokens generated successfully",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Invalid credentials or inactive user")
        }
    )
    def post(self, request, *args, **kwargs):
        logger.info("Received login request for email: %s", request.data.get('email'))
        try:
            response = super().post(request, *args, **kwargs)
            logger.info("Login successful for email: %s", request.data.get('email'))
            return response
        except Exception as e:
            logger.error("Login failed: %s", str(e))
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class RefreshTokenView(TokenRefreshView):
    @extend_schema(
        summary="Refresh JWT access token",
        description="Generates a new JWT access token using a valid refresh token.",
        responses={
            200: OpenApiResponse(
                description="Token refreshed successfully",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Invalid or expired refresh token")
        }
    )
    def post(self, request, *args, **kwargs):
        logger.info("Received token refresh request")
        try:
            response = super().post(request, *args, **kwargs)
            logger.info("Token refresh successful")
            return response
        except Exception as e:
            logger.error("Token refresh failed: %s", str(e))
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verify user email",
        description="Verifies the user's email by validating the token provided in the verification link. Activates the user account upon successful verification.",
        parameters=[
            {
                'name': 'token',
                'in': 'query',
                'required': True,
                'schema': {'type': 'string'},
                'description': 'The verification token sent in the email link.'
            },
            {
                'name': 'email',
                'in': 'query',
                'required': True,
                'schema': {'type': 'string', 'format': 'email'},
                'description': 'The email address to verify.'
            }
        ],
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description="Email verified successfully",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={
                            "user": {
                                "id": 1,
                                "first_name": "John",
                                "last_name": "Doe",
                                "username": "johndoe",
                                "email": "john.doe@example.com",
                                "is_active": True,
                                "is_admin": False,
                                "profile": {
                                    "date_of_birth": None,
                                    "gender": None,
                                    "phone_number": None,
                                    "avatar": None,
                                    "newsletter_subscription": True,
                                    "marketing_emails": True,
                                    "bio": None,
                                    "website": None
                                }
                            },
                            "message": "Email verified successfully."
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid or expired verification token, or user not found")
        }
    )
    def get(self, request):
        token = request.query_params.get('token')
        email = request.query_params.get('email')
        logger.info("Received email verification request for email: %s, token: %s", email, token)

        if not email or not token:
            logger.error("Email or token missing in verification request")
            return Response({'error': 'Email and token are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            serializer = EmailVerificationSerializer(data={'token': token, 'email': email})
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            logger.info("Email verified successfully for: %s", user.email)
            return Response({
                'message': _('Email verified successfully.'),
                'user': UserSerializer(user, context={'request': request}).data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Email verification failed for email %s: %s", email, str(e))
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ProfileRetrieveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve user profile",
        description="Retrieves the authenticated user's profile and basic information. Requires JWT authentication.",
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description="Profile retrieved successfully",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={
                            "id": 1,
                            "first_name": "John",
                            "last_name": "Doe",
                            "username": "johndoe",
                            "email": "john.doe@example.com",
                            "is_active": True,
                            "is_admin": False,
                            "profile": {
                                "date_of_birth": "1990-01-01",
                                "gender": "male",
                                "phone_number": "+1234567890",
                                "avatar": "/media/avatars/avatar.jpg",
                                "newsletter_subscription": True,
                                "marketing_emails": True,
                                "bio": "Software developer",
                                "website": "https://johndoe.com"
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Unauthorized")
        }
    )
    def get(self, request):
        logger.info("Received profile retrieve request for user: %s", request.user.email)
        try:
            user = request.user
            serializer = UserSerializer(user, context={'request': request})
            logger.info("Profile retrieved successfully for: %s", user.email)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Profile retrieve failed: %s", str(e))
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Update user profile",
        description="Updates the authenticated user's profile and basic information. Requires JWT authentication. Supports partial updates.",
        request=UserSerializer,
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description="Profile updated successfully",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={
                            "id": 1,
                            "first_name": "John",
                            "last_name": "Doe",
                            "username": "johndoe",
                            "email": "john.doe@example.com",
                            "is_active": True,
                            "is_admin": False,
                            "profile": {
                                "date_of_birth": "1990-01-01",
                                "gender": "male",
                                "phone_number": "+1234567890",
                                "avatar": "/media/avatars/avatar.jpg",
                                "newsletter_subscription": True,
                                "marketing_emails": True,
                                "bio": "Software developer",
                                "website": "https://johndoe.com"
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Unauthorized"),
            400: OpenApiResponse(description="Invalid input data")
        }
    )
    def put(self, request):
        logger.info("Received profile update request for user: %s", request.user.email)
        try:
            user = request.user
            serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            logger.info("Profile updated successfully for: %s", user.email)
            return Response(UserSerializer(user, context={'request': request}).data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Profile update failed: %s", str(e))
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserListView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="List all users",
        description="Retrieves a list of all users. Only accessible to admin users. Requires JWT authentication.",
        responses={
            200: OpenApiResponse(
                response=UserListSerializer(many=True),
                description="List of users retrieved successfully",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value=[
                            {
                                "id": 1,
                                "first_name": "John",
                                "last_name": "Doe",
                                "username": "johndoe",
                                "email": "john.doe@example.com",
                                "is_active": True,
                                "is_admin": False
                            },
                            {
                                "id": 2,
                                "first_name": "Jane",
                                "last_name": "Smith",
                                "username": "janesmith",
                                "email": "jane.smith@example.com",
                                "is_active": True,
                                "is_admin": True
                            }
                        ]
                    )
                ]
            ),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden (not an admin)")
        }
    )
    def get(self, request):
        logger.info("Received user list request from: %s", request.user.email)
        try:
            users = User.objects.all()
            serializer = UserListSerializer(users, many=True, context={'request': request})
            logger.info("User list retrieved successfully")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("User list retrieval failed: %s", str(e))
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)