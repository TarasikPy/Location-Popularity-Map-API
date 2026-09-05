from django.conf import settings
from django.db import models
from django.utils.text import slugify
from apps.common.models import SoftDeleteModel, TimeStampedModel


class Category(SoftDeleteModel, TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

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

    class Meta:
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.name
