import io
import json
import pandas as pd
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.locations.models import Category, Location
from apps.reviews.models import Review

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username='exporter', password='Password123!')


@pytest.fixture
def setup_data(db, user):
    cat_nature = Category.objects.create(name='Nature')
    cat_urban = Category.objects.create(name='Urban')

    loc1 = Location.objects.create(name='Forest Park', category=cat_nature, author=user, address='Woodland 1')
    loc2 = Location.objects.create(name='City Center', category=cat_urban, author=user, address='Main St 10')

    Review.objects.create(location=loc1, author=user, text='Peaceful', rating=5)
    return {'nature': cat_nature, 'urban': cat_urban, 'loc1': loc1, 'loc2': loc2}


@pytest.mark.django_db
def test_export_locations_csv(api_client, setup_data):
    url = reverse('location-export-csv')
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert 'text/csv' in response['Content-Type']
    assert response['Content-Disposition'] == 'attachment; filename="locations.csv"'

    # Verify content using pandas
    csv_stream = io.StringIO(response.content.decode('utf-8'))
    df = pd.read_csv(csv_stream)

    assert len(df) == 2
    assert 'name' in df.columns
    assert 'avg_rating' in df.columns
    assert 'popularity_score' in df.columns
    assert 'category' in df.columns

    forest_row = df[df['name'] == 'Forest Park'].iloc[0]
    assert forest_row['category'] == 'Nature'
    assert forest_row['avg_rating'] == 5.0
    assert forest_row['reviews_count'] == 1


@pytest.mark.django_db
def test_export_locations_json(api_client, setup_data):
    url = reverse('location-export-json')
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert 'application/json' in response['Content-Type']
    assert response['Content-Disposition'] == 'attachment; filename="locations.json"'

    data = json.loads(response.content.decode('utf-8'))
    assert len(data) == 2
    names = [item['name'] for item in data]
    assert 'Forest Park' in names
    assert 'City Center' in names


@pytest.mark.django_db
def test_export_locations_with_filter(api_client, setup_data):
    nature_cat = setup_data['nature']
    url = reverse('location-export-csv')
    response = api_client.get(url, {'category': nature_cat.id})

    assert response.status_code == status.HTTP_200_OK
    csv_stream = io.StringIO(response.content.decode('utf-8'))
    df = pd.read_csv(csv_stream)

    assert len(df) == 1
    assert df.iloc[0]['name'] == 'Forest Park'


@pytest.mark.django_db
def test_export_reviews_csv_and_json(api_client, setup_data):
    # CSV
    csv_url = reverse('review-export-csv')
    resp_csv = api_client.get(csv_url)
    assert resp_csv.status_code == status.HTTP_200_OK
    assert 'text/csv' in resp_csv['Content-Type']
    assert resp_csv['Content-Disposition'] == 'attachment; filename="reviews.csv"'

    df = pd.read_csv(io.StringIO(resp_csv.content.decode('utf-8')))
    assert len(df) == 1
    assert df.iloc[0]['text'] == 'Peaceful'
    assert df.iloc[0]['rating'] == 5

    # JSON
    json_url = reverse('review-export-json')
    resp_json = api_client.get(json_url)
    assert resp_json.status_code == status.HTTP_200_OK
    assert 'application/json' in resp_json['Content-Type']
    assert resp_json['Content-Disposition'] == 'attachment; filename="reviews.json"'

    json_data = json.loads(resp_json.content.decode('utf-8'))
    assert len(json_data) == 1
    assert json_data[0]['text'] == 'Peaceful'
