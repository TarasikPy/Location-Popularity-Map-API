from rest_framework import serializers
from apps.locations.models import Category, Location


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
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'author', 'author_id', 'created_at', 'updated_at')
