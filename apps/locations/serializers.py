from rest_framework import serializers
from apps.locations.models import Category, Location, LocationSubscription


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'created_at', 'updated_at')
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')


class LocationSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
    )
    author = serializers.ReadOnlyField(source='author.username')
    author_id = serializers.ReadOnlyField(source='author.id')
    avg_rating = serializers.FloatField(read_only=True, default=0.0)
    reviews_count = serializers.IntegerField(read_only=True, default=0)
    views_7d = serializers.IntegerField(read_only=True, default=0)
    views_count = serializers.IntegerField(read_only=True, default=0)
    popularity_score = serializers.FloatField(read_only=True, default=0.0)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = (
            'id',
            'name',
            'description',
            'address',
            'latitude',
            'longitude',
            'category',
            'category_id',
            'author',
            'author_id',
            'avg_rating',
            'reviews_count',
            'views_7d',
            'views_count',
            'popularity_score',
            'is_subscribed',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'author',
            'author_id',
            'avg_rating',
            'reviews_count',
            'views_7d',
            'views_count',
            'popularity_score',
            'is_subscribed',
            'created_at',
            'updated_at',
        )

    def get_is_subscribed(self, obj: Location) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.subscriptions.filter(user=request.user).exists()


class LocationSubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    user_id = serializers.ReadOnlyField(source='user.id')
    location_name = serializers.ReadOnlyField(source='location.name')
    location_id = serializers.ReadOnlyField(source='location.id')

    class Meta:
        model = LocationSubscription
        fields = ('id', 'location_id', 'location_name', 'user_id', 'user', 'created_at')
        read_only_fields = ('id', 'location_id', 'location_name', 'user_id', 'user', 'created_at')


