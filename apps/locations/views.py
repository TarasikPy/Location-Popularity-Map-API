from django.core.cache import cache
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.common.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from apps.locations.filters import LocationFilter
from apps.locations.models import Category, Location
from apps.locations.serializers import CategorySerializer, LocationSerializer
from apps.locations.services import (
    LOCATIONS_CACHE_TTL,
    get_locations_cache_key,
    record_location_view,
)


@extend_schema_view(
    list=extend_schema(tags=['Categories'], summary='List all active categories'),
    create=extend_schema(tags=['Categories'], summary='Create new category (Admin only)'),
    retrieve=extend_schema(tags=['Categories'], summary='Retrieve category details'),
    update=extend_schema(tags=['Categories'], summary='Update category (Admin only)'),
    partial_update=extend_schema(tags=['Categories'], summary='Partially update category (Admin only)'),
    destroy=extend_schema(tags=['Categories'], summary='Soft-delete category (Admin only)'),
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


@extend_schema_view(
    list=extend_schema(tags=['Locations'], summary='List all active locations'),
    create=extend_schema(tags=['Locations'], summary='Create new location (Authenticated users)'),
    retrieve=extend_schema(tags=['Locations'], summary='Retrieve location details'),
    update=extend_schema(tags=['Locations'], summary='Update location (Author or Admin only)'),
    partial_update=extend_schema(tags=['Locations'], summary='Partially update location (Author or Admin only)'),
    destroy=extend_schema(tags=['Locations'], summary='Soft-delete location (Author or Admin only)'),
)
class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LocationFilter
    search_fields = ['name', 'description', 'address']
    ordering_fields = [
        'created_at',
        'name',
        'avg_rating',
        'popularity_score',
        'reviews_count',
        'views_count',
    ]

    def get_queryset(self):
        return Location.objects.select_related('category', 'author').with_metrics().order_by('-created_at')

    def list(self, request, *args, **kwargs):
        cache_key = get_locations_cache_key(request.query_params)
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        if response.status_code == 200:
            cache.set(cache_key, response.data, timeout=LOCATIONS_CACHE_TTL)
        return response

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        is_new_view = record_location_view(instance, request)
        if is_new_view:
            if hasattr(instance, 'views_count'):
                instance.views_count += 1
            if hasattr(instance, 'views_7d'):
                instance.views_7d += 1
            if hasattr(instance, 'popularity_score'):
                instance.popularity_score += 1.0
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer: LocationSerializer) -> None:
        serializer.save(author=self.request.user)

    def perform_destroy(self, instance: Location) -> None:
        instance.delete()


