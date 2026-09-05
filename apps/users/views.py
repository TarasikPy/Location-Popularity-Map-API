from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


@extend_schema(
    tags=['Authentication'],
    summary='Obtain CSRF token and set cookie',
    responses={200: OpenApiResponse(description='CSRF cookie set successfully')}
)
class CSRFView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        token = get_token(request)
        return Response({'detail': 'CSRF cookie set', 'csrfToken': token})


@extend_schema(
    tags=['Authentication'],
    summary='Register a new user',
    request=RegisterSerializer,
    responses={201: UserSerializer}
)
class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Authentication'],
    summary='Log in user with session cookie',
    request=LoginSerializer,
    responses={200: UserSerializer}
)
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Authentication'],
    summary='Log out current user',
    responses={200: OpenApiResponse(description='Successfully logged out')}
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Authentication'],
    summary='Get currently logged-in user profile',
    responses={200: UserSerializer}
)
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


@extend_schema(
    tags=['Authentication'],
    summary='Request password reset token via email',
    request=PasswordResetRequestSerializer,
    responses={200: OpenApiResponse(description='Password reset email dispatched')}
)
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].lower()

        user = User.objects.filter(email__iexact=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            subject = 'Password Reset Request'
            message = (
                f'Hi {user.username},\n\n'
                f'Use the following credentials to reset your password:\n'
                f'UID: {uid}\n'
                f'Token: {token}\n'
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@locations.local'),
                recipient_list=[user.email],
                fail_silently=False,
            )

        return Response(
            {'detail': 'If an account with this email exists, password reset instructions have been sent.'},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=['Authentication'],
    summary='Reset password with token',
    request=PasswordResetConfirmSerializer,
    responses={200: OpenApiResponse(description='Password reset completed successfully')}
)
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
