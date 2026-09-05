import hashlib
from urllib.parse import urlencode
from django.core.cache import cache
from django.http import HttpRequest
from apps.common.redis import get_redis_client, set_rate_limit_nx
from apps.locations.models import Location, LocationView



def get_client_ip(request: HttpRequest) -> str:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def record_location_view(location: Location, request: HttpRequest) -> bool:
    user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    ip_address = get_client_ip(request)

    if user:
        rate_limit_key = f"view:loc:{location.id}:user:{user.id}"
    else:
        rate_limit_key = f"view:loc:{location.id}:ip:{ip_address}"

    is_unique = set_rate_limit_nx(key=rate_limit_key, value=1, timeout=3600)
    if not is_unique:
        return False

    client = get_redis_client()
    client.incr(f"views:loc:{location.id}")

    LocationView.objects.create(
        location=location,
        user=user,
        ip_address=ip_address,
    )
    return True


LOCATIONS_CACHE_PREFIX = 'locations:list'
LOCATIONS_CACHE_TTL = 3600


def get_locations_cache_key(query_params: dict) -> str:
    sorted_items = sorted((k, str(v)) for k, v in query_params.items())
    encoded = urlencode(sorted_items)
    param_hash = hashlib.md5(encoded.encode('utf-8')).hexdigest()
    return f"{LOCATIONS_CACHE_PREFIX}:{param_hash}"


def invalidate_locations_cache() -> None:
    cache.delete_pattern(f"{LOCATIONS_CACHE_PREFIX}:*")

