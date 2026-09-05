from datetime import timedelta
from django.apps import apps
from django.db.models import (
    Avg,
    Count,
    ExpressionWrapper,
    F,
    FloatField,
    IntegerField,
    OuterRef,
    Subquery,
    Value,
)
from django.db.models.functions import Cast, Coalesce
from django.utils import timezone
from apps.common.managers import SoftDeleteManager, SoftDeleteQuerySet


class LocationQuerySet(SoftDeleteQuerySet):
    def with_metrics(self):
        seven_days_ago = timezone.now() - timedelta(days=7)
        Review = apps.get_model('reviews', 'Review')
        LocationView = apps.get_model('locations', 'LocationView')

        reviews_sub = Review.objects.filter(location=OuterRef('pk')).order_by().values('location')
        avg_rating_sub = reviews_sub.annotate(val=Avg('rating')).values('val')
        reviews_count_sub = reviews_sub.annotate(val=Count('id')).values('val')

        views_sub = LocationView.objects.filter(location=OuterRef('pk')).order_by().values('location')
        views_7d_sub = LocationView.objects.filter(
            location=OuterRef('pk'),
            created_at__gte=seven_days_ago,
        ).order_by().values('location').annotate(val=Count('id')).values('val')
        views_count_sub = views_sub.annotate(val=Count('id')).values('val')

        return self.annotate(
            avg_rating=Coalesce(
                Subquery(avg_rating_sub, output_field=FloatField()),
                Value(0.0),
                output_field=FloatField(),
            ),
            reviews_count=Coalesce(
                Subquery(reviews_count_sub, output_field=IntegerField()),
                Value(0),
                output_field=IntegerField(),
            ),
            views_7d=Coalesce(
                Subquery(views_7d_sub, output_field=IntegerField()),
                Value(0),
                output_field=IntegerField(),
            ),
            views_count=Coalesce(
                Subquery(views_count_sub, output_field=IntegerField()),
                Value(0),
                output_field=IntegerField(),
            ),
        ).annotate(
            popularity_score=ExpressionWrapper(
                (F('avg_rating') * 10.0) +
                (Cast(F('reviews_count'), FloatField()) * 5.0) +
                (Cast(F('views_7d'), FloatField()) * 1.0),
                output_field=FloatField(),
            ),
        )


class LocationManager(SoftDeleteManager.from_queryset(LocationQuerySet)):
    pass

