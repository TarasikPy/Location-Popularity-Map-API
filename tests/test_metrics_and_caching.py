from datetime import timedelta
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.locations.models import Category, Location, LocationView
from apps.reviews.models import Review, ReviewReaction

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user1(db):
    return User.objects.create_user(username='u1', password='Password123!')


@pytest.fixture
def user2(db):
    return User.objects.create_user(username='u2', password='Password123!')


@pytest.fixture
def category(db):
    return Category.objects.create(name='Parks')


@pytest.mark.django_db
def test_dynamic_metrics_calculation(api_client, user1, user2, category):
    loc = Location.objects.create(name='Metric Park', category=category, author=user1)

    # 1. No reviews and no views
    resp = api_client.get(reverse('location-detail', kwargs={'pk': loc.pk}))
    # Note: retrieve adds 1 view (created right now, so views_7d=1, views_count=1, popularity_score=1.0)
    assert resp.data['avg_rating'] == 0.0
    assert resp.data['reviews_count'] == 0
    assert resp.data['views_7d'] == 1
    assert resp.data['views_count'] == 1
    assert resp.data['popularity_score'] == 1.0

    # 2. Add 2 reviews (rating 4 and 5)
    Review.objects.create(location=loc, author=user1, text='Good', rating=4)
    Review.objects.create(location=loc, author=user2, text='Excellent', rating=5)

    # 3. Add an old view (10 days ago) directly via DB
    old_time = timezone.now() - timedelta(days=10)
    old_view = LocationView.objects.create(location=loc, ip_address='10.0.0.99')
    LocationView.objects.filter(id=old_view.id).update(created_at=old_time)

    # Clear cache and check metrics via list
    cache.clear()
    list_resp = api_client.get(reverse('location-list'))
    data = list_resp.data['results'][0]

    # avg_rating = (4 + 5) / 2 = 4.5
    assert data['avg_rating'] == 4.5
    # reviews_count = 2
    assert data['reviews_count'] == 2
    # views_7d = 1 (only the first view within 7 days, old_view is 10 days ago)
    assert data['views_7d'] == 1
    # total views_count = 2 (today view + 10-days-ago view)
    assert data['views_count'] == 2
    # popularity_score = (4.5 * 10) + (2 * 5) + (1 * 1) = 45 + 10 + 1 = 56.0
    assert data['popularity_score'] == 56.0


@pytest.mark.django_db
def test_sorting_by_popularity_and_rating(api_client, user1, user2, category):
    loc_high = Location.objects.create(name='High Pop', category=category, author=user1)
    loc_low = Location.objects.create(name='Low Pop', category=category, author=user1)

    Review.objects.create(location=loc_high, author=user1, text='Great', rating=5)
    Review.objects.create(location=loc_high, author=user2, text='Awesome', rating=5)

    Review.objects.create(location=loc_low, author=user1, text='Okay', rating=2)

    # Sort by popularity descending
    resp_pop = api_client.get(reverse('location-list'), {'ordering': '-popularity_score'})
    results_pop = resp_pop.data['results']
    assert results_pop[0]['name'] == 'High Pop'
    assert results_pop[1]['name'] == 'Low Pop'
    assert results_pop[0]['popularity_score'] > results_pop[1]['popularity_score']

    # Sort by rating ascending
    resp_rating = api_client.get(reverse('location-list'), {'ordering': 'avg_rating'})
    results_rating = resp_rating.data['results']
    assert results_rating[0]['name'] == 'Low Pop'
    assert results_rating[1]['name'] == 'High Pop'


@pytest.mark.django_db
def test_redis_caching_and_auto_invalidation(api_client, user1, user2, category):
    loc = Location.objects.create(name='Cache Park', category=category, author=user1)
    list_url = reverse('location-list')

    # 1. First request fills cache
    resp1 = api_client.get(list_url)
    assert resp1.status_code == status.HTTP_200_OK
    assert resp1.data['results'][0]['reviews_count'] == 0

    # Verify keys exist in cache
    from apps.common.redis import get_redis_client
    client = get_redis_client()
    cache_keys = client.keys('locations:locations:list:*') or client.keys('*locations:list:*')
    assert len(cache_keys) > 0

    # 2. Creating a review triggers post_save signal and invalidates cache
    Review.objects.create(location=loc, author=user1, text='New Review', rating=5)

    # 3. Cache should be cleared, next request fetches fresh data
    resp2 = api_client.get(list_url)
    assert resp2.data['results'][0]['reviews_count'] == 1
    assert resp2.data['results'][0]['avg_rating'] == 5.0

    # 4. Modifying location also invalidates cache
    loc.name = 'Renamed Cache Park'
    loc.save()

    resp3 = api_client.get(list_url)
    assert resp3.data['results'][0]['name'] == 'Renamed Cache Park'
