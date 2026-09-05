from datetime import timedelta
from django.db.models import Avg, Count, ExpressionWrapper, F, FloatField, Q, Value
from django.db.models.functions import Cast, Coalesce
from django.utils import timezone
from apps.common.managers import SoftDeleteManager, SoftDeleteQuerySet


class LocationQuerySet(SoftDeleteQuerySet):
    def with_metrics(self):
        seven_days_ago = timezone.now() - timedelta(days=7)
        return self.annotate(
            avg_rating=Coalesce(
                Avg('reviews__rating'),
                Value(0.0),
                output_field=FloatField(),
            ),
            reviews_count=Count('reviews', distinct=True),
            views_7d=Count('views', filter=Q(views__created_at__gte=seven_days_ago), distinct=True),
            views_count=Count('views', distinct=True),
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
