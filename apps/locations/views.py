from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.common.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from apps.locations.filters import LocationFilter
from apps.locations.models import Category, Location
from apps.locations.serializers import CategorySerializer, LocationSerializer
from apps.locations.services import record_location_view


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
    ordering_fields = ['created_at', 'name']

    def get_queryset(self):
        return Location.objects.select_related('category', 'author').annotate(
            views_count=Count('views', distinct=True),
        ).order_by('-created_at')


    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        is_new_view = record_location_view(instance, request)
        if is_new_view and hasattr(instance, 'views_count'):
            instance.views_count += 1
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer: LocationSerializer) -> None:
        serializer.save(author=self.request.user)

    def perform_destroy(self, instance: Location) -> None:
        instance.delete()

