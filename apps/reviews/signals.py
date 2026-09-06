from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from apps.locations.services import invalidate_locations_cache
from apps.reviews.models import Review, ReviewReaction
from apps.reviews.services import notify_author_and_subscribers_on_new_review


@receiver(post_save, sender=Review)
def on_review_saved(sender, instance, created, **kwargs):
    invalidate_locations_cache()
    if created:
        notify_author_and_subscribers_on_new_review(instance)


@receiver(post_delete, sender=Review)
def on_review_deleted(sender, instance, **kwargs):
    invalidate_locations_cache()


@receiver([post_save, post_delete], sender=ReviewReaction)
def on_review_reaction_changed(sender, instance, **kwargs):
    invalidate_locations_cache()
