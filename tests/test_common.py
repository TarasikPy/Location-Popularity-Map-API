import pytest
from django.db import connection, models
from apps.common.models import SoftDeleteModel, TimeStampedModel
from apps.common.redis import get_redis_client, set_rate_limit_nx


class DummyItem(SoftDeleteModel, TimeStampedModel):
    name = models.CharField(max_length=50)

    class Meta:
        app_label = 'common'


@pytest.fixture(scope='function')
def dummy_model(db):
    with connection.cursor() as cursor:
        cursor.execute('DROP TABLE IF EXISTS common_dummyitem CASCADE;')
    with connection.schema_editor() as editor:
        editor.create_model(DummyItem)
    yield
    with connection.schema_editor() as editor:
        editor.delete_model(DummyItem)


def test_redis_rate_limit_atomic():
    key = 'test:rate:limit:common'
    client = get_redis_client()
    client.delete(key)

    assert set_rate_limit_nx(key, timeout=10) is True
    assert set_rate_limit_nx(key, timeout=10) is False

    client.delete(key)


def test_soft_delete_lifecycle(dummy_model):
    item = DummyItem.objects.create(name='Item 1')

    assert DummyItem.objects.count() == 1
    assert DummyItem.all_objects.count() == 1
    assert item.created_at is not None
    assert item.is_deleted is False

    # Soft delete single instance
    item.delete()
    assert DummyItem.objects.count() == 0
    assert DummyItem.all_objects.count() == 1
    item.refresh_from_db()
    assert item.is_deleted is True
    assert item.deleted_at is not None

    # Restore
    item.restore()
    assert DummyItem.objects.count() == 1
    item.refresh_from_db()
    assert item.is_deleted is False
    assert item.deleted_at is None

    # QuerySet delete
    DummyItem.objects.filter(id=item.id).delete()
    assert DummyItem.objects.count() == 0
    assert DummyItem.all_objects.count() == 1

    # Hard delete
    item.hard_delete()
    assert DummyItem.all_objects.count() == 0
