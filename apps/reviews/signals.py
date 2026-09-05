from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from apps.locations.services import invalidate_locations_cache
from apps.reviews.models import Review, ReviewReaction


@receiver([post_save, post_delete], sender=Review)
def on_review_changed(sender, instance, **kwargs):
    invalidate_locations_cache()


@receiver([post_save, post_delete], sender=ReviewReaction)
def on_review_reaction_changed(sender, instance, **kwargs):
    invalidate_locations_cache()
