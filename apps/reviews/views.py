from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.common.permissions import IsAuthorOrReadOnly
from apps.reviews.models import Review, ReviewReaction
from apps.reviews.serializers import ReviewReactionSerializer, ReviewSerializer


@extend_schema_view(
    list=extend_schema(tags=['Reviews'], summary='List all reviews'),
    create=extend_schema(tags=['Reviews'], summary='Create a review (Authenticated, 1 per location)'),
    retrieve=extend_schema(tags=['Reviews'], summary='Retrieve review details'),
    update=extend_schema(tags=['Reviews'], summary='Update review (Author or Admin only)'),
    partial_update=extend_schema(tags=['Reviews'], summary='Partially update review (Author or Admin only)'),
    destroy=extend_schema(tags=['Reviews'], summary='Delete review (Author or Admin only)'),
)
class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['location', 'rating']
    ordering_fields = ['created_at', 'rating', 'likes_count']

    def get_queryset(self):
        return Review.objects.select_related('author', 'location').annotate(
            likes_count=Count('reactions', filter=Q(reactions__reaction=ReviewReaction.ReactionType.LIKE), distinct=True),
            dislikes_count=Count('reactions', filter=Q(reactions__reaction=ReviewReaction.ReactionType.DISLIKE), distinct=True),
        ).order_by('-created_at')

    def perform_create(self, serializer: ReviewSerializer) -> None:
        serializer.save(author=self.request.user)

    @extend_schema(
        tags=['Reviews'],
        summary='Add or update like/dislike reaction on a review',
        request=ReviewReactionSerializer,
        responses={200: ReviewReactionSerializer},
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def react(self, request, pk=None):
        review = self.get_object()
        serializer = ReviewReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reaction_value = serializer.validated_data['reaction']
        ReviewReaction.objects.update_or_create(
            review=review,
            user=request.user,
            defaults={'reaction': reaction_value},
        )
        return Response(
            {'detail': 'Reaction recorded.', 'reaction': reaction_value},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=['Reviews'],
        summary='Remove user reaction from a review',
        responses={200: dict},
    )
    @react.mapping.delete
    def remove_reaction(self, request, pk=None):
        review = self.get_object()
        ReviewReaction.objects.filter(review=review, user=request.user).delete()
        return Response({'detail': 'Reaction removed.'}, status=status.HTTP_200_OK)
