from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from apps.common.models import TimeStampedModel


class Review(TimeStampedModel):
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['location', 'author'],
                name='unique_user_location_review',
            ),
        ]

    def __str__(self) -> str:
        return f"Review by {self.author_id} for location {self.location_id} ({self.rating})"


class ReviewReaction(TimeStampedModel):
    class ReactionType(models.TextChoices):
        LIKE = 'like', 'Like'
        DISLIKE = 'dislike', 'Dislike'

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='reactions',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_reactions',
    )
    reaction = models.CharField(
        max_length=10,
        choices=ReactionType.choices,
    )

    class Meta:
        verbose_name = 'Review Reaction'
        verbose_name_plural = 'Review Reactions'
        constraints = [
            models.UniqueConstraint(
                fields=['review', 'user'],
                name='unique_user_review_reaction',
            ),
        ]

    def __str__(self) -> str:
        return f"{self.reaction} by {self.user_id} on review {self.review_id}"
