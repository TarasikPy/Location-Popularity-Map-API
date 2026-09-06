from django_filters import rest_framework as filters
from apps.locations.models import Location


class LocationFilter(filters.FilterSet):
    category = filters.NumberFilter(field_name='category_id')
    category_slug = filters.CharFilter(field_name='category__slug')
    author = filters.NumberFilter(field_name='author_id')
    author_username = filters.CharFilter(field_name='author__username', lookup_expr='iexact')
    rating = filters.NumberFilter(field_name='avg_rating', lookup_expr='exact')
    min_rating = filters.NumberFilter(field_name='avg_rating', lookup_expr='gte')
    max_rating = filters.NumberFilter(field_name='avg_rating', lookup_expr='lte')

    class Meta:
        model = Location
        fields = (
            'category',
            'category_slug',
            'author',
            'author_username',
            'rating',
            'min_rating',
            'max_rating',
        )
