from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from django_filters.rest_framework import DjangoFilterBackend

from apps.common.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from apps.locations.filters import LocationFilter
from apps.locations.models import Category, Location
from apps.locations.serializers import CategorySerializer, LocationSerializer


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
    queryset = Location.objects.select_related('category', 'author').all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LocationFilter
    search_fields = ['name', 'description', 'address']
    ordering_fields = ['created_at', 'name']

    def perform_create(self, serializer: LocationSerializer) -> None:
        serializer.save(author=self.request.user)

    def perform_destroy(self, instance: Location) -> None:
        instance.delete()
