from django_filters import rest_framework as filters
from apps.locations.models import Location


class LocationFilter(filters.FilterSet):
    category = filters.NumberFilter(field_name='category_id')
    category_slug = filters.CharFilter(field_name='category__slug')

    class Meta:
        model = Location
        fields = ('category', 'category_slug')
