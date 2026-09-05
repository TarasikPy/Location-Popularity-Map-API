import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.locations.models import Category, Location
from apps.reviews.models import Review, ReviewReaction

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user1(db):
    return User.objects.create_user(username='user1', password='Password123!')


@pytest.fixture
def user2(db):
    return User.objects.create_user(username='user2', password='Password123!')


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(username='admin', password='Password123!')


@pytest.fixture
def location(db, user1):
    cat = Category.objects.create(name='Parks')
    return Location.objects.create(name='Park', description='Desc', category=cat, author=user1)


@pytest.fixture
def location2(db, user1):
    cat = Category.objects.get(name='Parks')
    return Location.objects.create(name='Park 2', description='Desc 2', category=cat, author=user1)


@pytest.mark.django_db
def test_rating_validation(api_client, user1, location):
    api_client.force_login(user1)
    url = reverse('review-list')

    # Rating 0 (invalid)
    resp_low = api_client.post(url, data={'location_id': location.id, 'text': 'Bad', 'rating': 0})
    assert resp_low.status_code == status.HTTP_400_BAD_REQUEST

    # Rating 6 (invalid)
    resp_high = api_client.post(url, data={'location_id': location.id, 'text': 'Over', 'rating': 6})
    assert resp_high.status_code == status.HTTP_400_BAD_REQUEST

    # Rating 5 (valid)
    resp_valid = api_client.post(url, data={'location_id': location.id, 'text': 'Great!', 'rating': 5})
    assert resp_valid.status_code == status.HTTP_201_CREATED
    assert resp_valid.data['rating'] == 5


@pytest.mark.django_db
def test_one_review_per_location_limit(api_client, user1, location, location2):
    api_client.force_login(user1)
    url = reverse('review-list')

    # First review on location 1 succeeds
    resp1 = api_client.post(url, data={'location_id': location.id, 'text': 'First review', 'rating': 4})
    assert resp1.status_code == status.HTTP_201_CREATED

    # Second review on same location 1 by user1 fails
    resp2 = api_client.post(url, data={'location_id': location.id, 'text': 'Duplicate review', 'rating': 3})
    assert resp2.status_code == status.HTTP_400_BAD_REQUEST
    assert 'detail' in resp2.data

    # Review on different location 2 succeeds
    resp3 = api_client.post(url, data={'location_id': location2.id, 'text': 'Review loc 2', 'rating': 5})
    assert resp3.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_review_permissions(api_client, user1, user2, admin_user, location):
    # Anonymous cannot create review
    url = reverse('review-list')
    resp_anon = api_client.post(url, data={'location_id': location.id, 'text': 'Anon', 'rating': 4})
    assert resp_anon.status_code == status.HTTP_403_FORBIDDEN

    # User 1 creates review
    api_client.force_login(user1)
    create_resp = api_client.post(url, data={'location_id': location.id, 'text': 'User1 review', 'rating': 4})
    review_id = create_resp.data['id']
    detail_url = reverse('review-detail', kwargs={'pk': review_id})

    # User 2 cannot edit or delete user 1's review
    api_client.force_login(user2)
    patch_resp = api_client.patch(detail_url, data={'text': 'Hacked'})
    assert patch_resp.status_code == status.HTTP_403_FORBIDDEN
    del_resp = api_client.delete(detail_url)
    assert del_resp.status_code == status.HTTP_403_FORBIDDEN

    # User 1 can update their review
    api_client.force_login(user1)
    patch_resp2 = api_client.patch(detail_url, data={'text': 'Updated text'})
    assert patch_resp2.status_code == status.HTTP_200_OK
    assert patch_resp2.data['text'] == 'Updated text'

    # Admin can delete review
    api_client.force_login(admin_user)
    admin_del = api_client.delete(detail_url)
    assert admin_del.status_code == status.HTTP_204_NO_CONTENT
    assert Review.objects.filter(id=review_id).count() == 0


@pytest.mark.django_db
def test_review_reactions_like_dislike(api_client, user1, user2, location):
    # Create review by user1
    review = Review.objects.create(location=location, author=user1, text='Awesome place', rating=5)
    react_url = reverse('review-react', kwargs={'pk': review.pk})

    # User2 likes the review
    api_client.force_login(user2)
    resp_like = api_client.post(react_url, data={'reaction': 'like'})
    assert resp_like.status_code == status.HTTP_200_OK

    detail_url = reverse('review-detail', kwargs={'pk': review.pk})
    resp_detail = api_client.get(detail_url)
    assert resp_detail.data['likes_count'] == 1
    assert resp_detail.data['dislikes_count'] == 0
    assert resp_detail.data['user_reaction'] == 'like'

    # User2 changes reaction to dislike
    resp_dislike = api_client.post(react_url, data={'reaction': 'dislike'})
    assert resp_dislike.status_code == status.HTTP_200_OK

    resp_detail2 = api_client.get(detail_url)
    assert resp_detail2.data['likes_count'] == 0
    assert resp_detail2.data['dislikes_count'] == 1
    assert resp_detail2.data['user_reaction'] == 'dislike'

    # User2 removes reaction
    resp_remove = api_client.delete(react_url)
    assert resp_remove.status_code == status.HTTP_200_OK

    resp_detail3 = api_client.get(detail_url)
    assert resp_detail3.data['likes_count'] == 0
    assert resp_detail3.data['dislikes_count'] == 0
    assert resp_detail3.data['user_reaction'] is None
