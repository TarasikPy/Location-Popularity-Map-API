import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='StrongPassword123!',
    )


@pytest.mark.django_db
def test_csrf_endpoint(api_client):
    response = api_client.get(reverse('auth-csrf'))
    assert response.status_code == status.HTTP_200_OK
    assert 'csrfToken' in response.data
    assert 'csrftoken' in response.cookies


@pytest.mark.django_db
def test_user_registration(api_client):
    data = {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'SecurePassword123!',
        'password_confirm': 'SecurePassword123!',
    }
    response = api_client.post(reverse('auth-register'), data=data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['username'] == 'newuser'
    assert response.data['email'] == 'newuser@example.com'
    assert 'sessionid' in response.cookies
    assert User.objects.filter(username='newuser').exists()


@pytest.mark.django_db
def test_registration_password_mismatch(api_client):
    data = {
        'username': 'mismatchuser',
        'email': 'mismatch@example.com',
        'password': 'Password123!',
        'password_confirm': 'DifferentPassword123!',
    }
    response = api_client.post(reverse('auth-register'), data=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'password_confirm' in response.data


@pytest.mark.django_db
def test_login_and_me_lifecycle(api_client, test_user):
    # Before login, me is forbidden/unauthenticated
    me_resp_pre = api_client.get(reverse('auth-me'))
    assert me_resp_pre.status_code == status.HTTP_403_FORBIDDEN

    # Login
    login_resp = api_client.post(
        reverse('auth-login'),
        data={'username': 'testuser', 'password': 'StrongPassword123!'},
    )
    assert login_resp.status_code == status.HTTP_200_OK
    assert 'sessionid' in login_resp.cookies

    # Me is now accessible
    me_resp_post = api_client.get(reverse('auth-me'))
    assert me_resp_post.status_code == status.HTTP_200_OK
    assert me_resp_post.data['username'] == 'testuser'
    assert me_resp_post.data['email'] == 'testuser@example.com'

    # Logout
    logout_resp = api_client.post(reverse('auth-logout'))
    assert logout_resp.status_code == status.HTTP_200_OK

    # Me is forbidden again
    me_resp_after = api_client.get(reverse('auth-me'))
    assert me_resp_after.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_password_reset_flow(api_client, test_user):
    # Request reset email
    response = api_client.post(
        reverse('auth-password-reset'),
        data={'email': 'testuser@example.com'},
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1
    assert 'Password Reset Request' in mail.outbox[0].subject

    # Confirm password reset
    uid = urlsafe_base64_encode(force_bytes(test_user.pk))
    token = default_token_generator.make_token(test_user)
    new_password = 'BrandNewPassword123!'

    confirm_resp = api_client.post(
        reverse('auth-password-reset-confirm'),
        data={
            'uid': uid,
            'token': token,
            'new_password': new_password,
            'new_password_confirm': new_password,
        },
    )
    assert confirm_resp.status_code == status.HTTP_200_OK

    # Verify new password can log in
    test_user.refresh_from_db()
    assert test_user.check_password(new_password)
