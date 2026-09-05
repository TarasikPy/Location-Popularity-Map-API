import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.locations.models import Category, Location

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def author(db):
    return User.objects.create_user(username='author', email='author@test.com', password='Password123!')


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username='other', email='other@test.com', password='Password123!')


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(username='admin', email='admin@test.com', password='Password123!')


@pytest.fixture
def category(db):
    return Category.objects.create(name='Parks', description='City parks and nature')


@pytest.fixture
def location(db, author, category):
    return Location.objects.create(
        name='Central Park',
        description='A large urban park',
        address='123 Park Ave',
        category=category,
        author=author,
    )


@pytest.mark.django_db
def test_category_permissions(api_client, author, admin_user):
    # Anonymous can read
    resp = api_client.get(reverse('category-list'))
    assert resp.status_code == status.HTTP_200_OK

    # Regular user cannot create
    api_client.force_login(author)
    resp = api_client.post(reverse('category-list'), data={'name': 'Museums'})
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    # Admin can create
    api_client.force_login(admin_user)
    resp = api_client.post(reverse('category-list'), data={'name': 'Museums', 'description': 'Historical museums'})
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.data['slug'] == 'museums'


@pytest.mark.django_db
def test_location_creation_and_author_assignment(api_client, author, category):
    # Anonymous cannot create
    resp = api_client.post(reverse('location-list'), data={'name': 'Anon Place', 'category_id': category.id})
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    # Authenticated user creates
    api_client.force_login(author)
    data = {
        'name': 'Golden Gate',
        'description': 'Famous bridge and park area',
        'address': 'San Francisco, CA',
        'latitude': '37.819900',
        'longitude': '-122.478300',
        'category_id': category.id,
    }
    resp = api_client.post(reverse('location-list'), data=data)
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.data['name'] == 'Golden Gate'
    assert resp.data['author'] == author.username
    assert resp.data['author_id'] == author.id
    assert resp.data['category']['name'] == 'Parks'


@pytest.mark.django_db
def test_location_update_and_delete_permissions(api_client, author, other_user, admin_user, location):
    # Other user cannot update or delete
    api_client.force_login(other_user)
    update_url = reverse('location-detail', kwargs={'pk': location.pk})
    resp = api_client.patch(update_url, data={'name': 'Hacked Park'})
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    resp = api_client.delete(update_url)
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    # Author can update
    api_client.force_login(author)
    resp = api_client.patch(update_url, data={'name': 'Updated Central Park'})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data['name'] == 'Updated Central Park'

    # Admin can delete
    api_client.force_login(admin_user)
    del_resp = api_client.delete(update_url)
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # Soft delete verification
    assert Location.objects.filter(pk=location.pk).count() == 0
    assert Location.all_objects.filter(pk=location.pk).count() == 1
    deleted_loc = Location.all_objects.get(pk=location.pk)
    assert deleted_loc.is_deleted is True
    assert deleted_loc.deleted_at is not None


@pytest.mark.django_db
def test_location_category_filtering(api_client, author):
    cat_cafes = Category.objects.create(name='Cafes')
    cat_parks = Category.objects.create(name='Parks')

    Location.objects.create(name='Cafe 1', description='Desc', category=cat_cafes, author=author)
    Location.objects.create(name='Park 1', description='Desc', category=cat_parks, author=author)

    # Filter by category id
    resp = api_client.get(reverse('location-list'), {'category': cat_cafes.id})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data['count'] == 1
    assert resp.data['results'][0]['name'] == 'Cafe 1'

    # Filter by category slug
    resp = api_client.get(reverse('location-list'), {'category_slug': 'parks'})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data['count'] == 1
    assert resp.data['results'][0]['name'] == 'Park 1'
