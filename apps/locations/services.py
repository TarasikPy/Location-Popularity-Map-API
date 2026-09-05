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
