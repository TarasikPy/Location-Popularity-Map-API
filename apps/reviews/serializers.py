from rest_framework import serializers
from apps.locations.models import Location
from apps.reviews.models import Review, ReviewReaction


class ReviewReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewReaction
        fields = ('reaction',)


class ReviewSerializer(serializers.ModelSerializer):
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source='location',
    )
    author = serializers.ReadOnlyField(source='author.username')
    author_id = serializers.ReadOnlyField(source='author.id')
    likes_count = serializers.IntegerField(read_only=True, default=0)
    dislikes_count = serializers.IntegerField(read_only=True, default=0)
    user_reaction = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            'id',
            'location_id',
            'author',
            'author_id',
            'rating',
            'text',
            'likes_count',
            'dislikes_count',
            'user_reaction',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'author',
            'author_id',
            'likes_count',
            'dislikes_count',
            'user_reaction',
            'created_at',
            'updated_at',
        )

    def get_user_reaction(self, obj: Review) -> str | None:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        # Use prefetched reaction if available, else query
        reactions = getattr(obj, 'prefetched_user_reaction', None)
        if reactions is not None:
            return reactions[0].reaction if reactions else None
        reaction_obj = obj.reactions.filter(user=request.user).first()
        return reaction_obj.reaction if reaction_obj else None

    def validate(self, attrs: dict) -> dict:
        request = self.context.get('request')
        if request and request.method == 'POST':
            location = attrs.get('location')
            if Review.objects.filter(location=location, author=request.user).exists():
                raise serializers.ValidationError({'detail': 'You have already reviewed this location.'})
        return attrs
