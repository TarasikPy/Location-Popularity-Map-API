import hashlib
from urllib.parse import urlencode
import pandas as pd
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
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


def export_locations_to_csv(queryset) -> HttpResponse:
    data = [
        {
            'id': loc.id,
            'name': loc.name,
            'category': loc.category.name if loc.category else '',
            'author': loc.author.username if loc.author else '',
            'avg_rating': round(getattr(loc, 'avg_rating', 0.0), 2),
            'reviews_count': getattr(loc, 'reviews_count', 0),
            'views_7d': getattr(loc, 'views_7d', 0),
            'views_count': getattr(loc, 'views_count', 0),
            'popularity_score': round(getattr(loc, 'popularity_score', 0.0), 2),
            'latitude': str(loc.latitude) if loc.latitude is not None else '',
            'longitude': str(loc.longitude) if loc.longitude is not None else '',
            'address': loc.address,
            'created_at': loc.created_at.isoformat() if loc.created_at else '',
        }
        for loc in queryset
    ]
    df = pd.DataFrame(data)
    csv_data = df.to_csv(index=False)
    response = HttpResponse(csv_data, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="locations.csv"'
    return response


def export_locations_to_json(queryset) -> HttpResponse:
    data = [
        {
            'id': loc.id,
            'name': loc.name,
            'category': loc.category.name if loc.category else '',
            'author': loc.author.username if loc.author else '',
            'avg_rating': round(getattr(loc, 'avg_rating', 0.0), 2),
            'reviews_count': getattr(loc, 'reviews_count', 0),
            'views_7d': getattr(loc, 'views_7d', 0),
            'views_count': getattr(loc, 'views_count', 0),
            'popularity_score': round(getattr(loc, 'popularity_score', 0.0), 2),
            'latitude': str(loc.latitude) if loc.latitude is not None else '',
            'longitude': str(loc.longitude) if loc.longitude is not None else '',
            'address': loc.address,
            'created_at': loc.created_at.isoformat() if loc.created_at else '',
        }
        for loc in queryset
    ]
    df = pd.DataFrame(data)
    json_data = df.to_json(orient='records', indent=2, force_ascii=False)
    response = HttpResponse(json_data, content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="locations.json"'
    return response


