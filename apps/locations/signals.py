from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from apps.locations.models import Location
from apps.locations.services import invalidate_locations_cache


@receiver([post_save, post_delete], sender=Location)
def on_location_changed(sender, instance, **kwargs):
    invalidate_locations_cache()
