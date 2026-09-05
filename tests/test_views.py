import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.common.redis import get_redis_client
from apps.locations.models import Category, Location, LocationView

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def clean_redis():
    client = get_redis_client()
    client.flushdb()
    yield
    client.flushdb()


@pytest.fixture
def location(db):
    author = User.objects.create_user(username='author', password='Password123!')
    category = Category.objects.create(name='Parks')
    return Location.objects.create(
        name='Central Park',
        description='A park in the city',
        category=category,
        author=author,
    )


@pytest.mark.django_db
def test_anonymous_view_rate_limit_by_ip(api_client, location):
    url = reverse('location-detail', kwargs={'pk': location.pk})

    # 1. First visit from IP 192.168.1.1
    resp1 = api_client.get(url, REMOTE_ADDR='192.168.1.1')
    assert resp1.status_code == status.HTTP_200_OK
    assert resp1.data['views_count'] == 1
    assert LocationView.objects.filter(location=location).count() == 1

    # 2. Repeated visit within 1 hour from same IP -> does NOT increment
    resp2 = api_client.get(url, REMOTE_ADDR='192.168.1.1')
    assert resp2.status_code == status.HTTP_200_OK
    assert resp2.data['views_count'] == 1
    assert LocationView.objects.filter(location=location).count() == 1

    # 3. Visit from different IP -> increments
    resp3 = api_client.get(url, REMOTE_ADDR='192.168.1.2')
    assert resp3.status_code == status.HTTP_200_OK
    assert resp3.data['views_count'] == 2
    assert LocationView.objects.filter(location=location).count() == 2


@pytest.mark.django_db
def test_authenticated_view_rate_limit_by_user(api_client, location):
    user1 = User.objects.create_user(username='user1', password='Password123!')
    user2 = User.objects.create_user(username='user2', password='Password123!')
    url = reverse('location-detail', kwargs={'pk': location.pk})

    # 1. First visit by user1
    api_client.force_login(user1)
    resp1 = api_client.get(url)
    assert resp1.status_code == status.HTTP_200_OK
    assert resp1.data['views_count'] == 1
    assert LocationView.objects.filter(location=location, user=user1).count() == 1

    # 2. Second visit by user1 within 1 hour -> no increment
    resp2 = api_client.get(url)
    assert resp2.status_code == status.HTTP_200_OK
    assert resp2.data['views_count'] == 1
    assert LocationView.objects.filter(location=location).count() == 1

    # 3. Visit by user2 -> increments
    api_client.force_login(user2)
    resp3 = api_client.get(url)
    assert resp3.status_code == status.HTTP_200_OK
    assert resp3.data['views_count'] == 2
    assert LocationView.objects.filter(location=location, user=user2).count() == 1


@pytest.mark.django_db
def test_redis_ttl_for_view_rate_limit(api_client, location):
    url = reverse('location-detail', kwargs={'pk': location.pk})
    ip = '10.0.0.5'

    api_client.get(url, REMOTE_ADDR=ip)

    client = get_redis_client()
    key = f'view:loc:{location.pk}:ip:{ip}'
    ttl = client.ttl(key)

    assert ttl > 0
    assert ttl <= 3600
    assert client.get(f'views:loc:{location.pk}') == b'1'
