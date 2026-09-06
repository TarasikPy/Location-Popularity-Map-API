from django.conf import settings
from django.db import models
from django.utils.text import slugify
from apps.common.models import SoftDeleteModel, TimeStampedModel
from apps.locations.managers import LocationManager



class Category(SoftDeleteModel, TimeStampedModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                condition=models.Q(is_deleted=False),
                name='unique_active_category_name',
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Location(SoftDeleteModel, TimeStampedModel):
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='locations',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='locations',
    )

    objects = LocationManager()

    class Meta:

        verbose_name = 'Location'
        verbose_name_plural = 'Locations'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.name


class LocationView(models.Model):
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='views',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='location_views',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Location View'
        verbose_name_plural = 'Location Views'
        indexes = [
            models.Index(fields=['location', 'created_at']),
        ]

    def __str__(self) -> str:
        return f"View for {self.location_id} at {self.created_at}"


class LocationSubscription(TimeStampedModel):
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='location_subscriptions',
    )

    class Meta:
        verbose_name = 'Location Subscription'
        verbose_name_plural = 'Location Subscriptions'
        constraints = [
            models.UniqueConstraint(
                fields=['location', 'user'],
                name='unique_user_location_subscription',
            ),
        ]

    def __str__(self) -> str:
        return f"Subscription of {self.user_id} to {self.location_id}"

