from typing import Any
from django_redis import get_redis_connection
from redis import Redis


def get_redis_client() -> Redis:
    return get_redis_connection('default')


def set_rate_limit_nx(key: str, value: Any = 1, timeout: int = 3600) -> bool:
    client = get_redis_client()
    return bool(client.set(name=key, value=value, ex=timeout, nx=True))
