from datetime import datetime, timezone
from unittest.mock import MagicMock

from chainlogistics_sdk.client import ChainLogisticsClient
from chainlogistics_sdk.config import Config
from chainlogistics_sdk.models import (
    EventListQuery,
    NewProduct,
    NewTrackingEvent,
    ProductListQuery,
    UpdateProduct,
)


def build_client() -> ChainLogisticsClient:
    return ChainLogisticsClient(Config("test-key", base_url="https://example.com"))


def product_payload(product_id: str = "prod-1") -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": product_id,
        "name": "Widget",
        "description": "Tracked product",
        "origin_location": "Lagos",
        "category": "Food",
        "tags": ["cold-chain"],
        "certifications": ["iso"],
        "media_hashes": [],
        "custom_fields": {},
        "owner_address": "owner-1",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "created_by": "user-1",
        "updated_by": "user-1",
    }


def event_payload() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": 1,
        "product_id": "prod-1",
        "actor_address": "actor-1",
        "timestamp": now,
        "event_type": "CREATED",
        "location": "Warehouse",
        "data_hash": "hash",
        "note": "Created",
        "metadata": {},
        "created_at": now,
    }


def test_products_list_builds_models_and_pagination():
    client = build_client()
    client.get = MagicMock(
        return_value={
            "products": [product_payload()],
            "total": 1,
            "offset": 0,
            "limit": 20,
        }
    )

    products, pagination = client.products.list(ProductListQuery(limit=20, is_active=True))

    assert products[0].id == "prod-1"
    assert pagination.total == 1


def test_product_service_convenience_methods_delegate_correctly():
    client = build_client()
    client.get = MagicMock(
        side_effect=[
            product_payload("prod-2"),
            {"products": [product_payload("prod-3")], "total": 1, "offset": 0, "limit": 5},
            {"products": [product_payload("prod-4")], "total": 1, "offset": 0, "limit": 5},
            {"products": [product_payload("prod-5")], "total": 1, "offset": 0, "limit": 5},
        ]
    )
    client.post = MagicMock(return_value=product_payload("prod-6"))
    client.put = MagicMock(return_value=product_payload("prod-7"))
    client.delete = MagicMock(return_value=None)

    assert client.products.get("prod-2").id == "prod-2"
    assert client.products.search("coffee")[0].id == "prod-3"
    assert client.products.list_by_owner("owner-1")[0][0].id == "prod-4"
    assert client.products.list_by_category("Food")[0][0].id == "prod-5"
    assert client.products.create.__call__ is not None

    created = client.products.create(NewProduct(**{
        "id": "prod-6",
        "name": "Widget",
        "description": "Tracked product",
        "origin_location": "Lagos",
        "category": "Food",
        "tags": [],
        "certifications": [],
        "media_hashes": [],
        "custom_fields": {},
        "owner_address": "owner-1",
        "created_by": "user-1",
    }))
    updated = client.products.update(
        "prod-7",
        UpdateProduct(updated_by="user-1"),
    )
    client.products.delete("prod-7")

    assert created.id == "prod-6"
    assert updated.id == "prod-7"
    client.delete.assert_called_once()


def test_events_list_by_product_maps_response():
    client = build_client()
    client.get = MagicMock(
        return_value={
            "events": [event_payload()],
            "total": 1,
            "offset": 0,
            "limit": 10,
        }
    )

    events, pagination = client.events.list(EventListQuery(product_id="prod-1"))

    assert events[0].event_type == "CREATED"
    assert pagination.limit == 10


def test_event_service_convenience_methods_delegate_correctly():
    client = build_client()
    client.get = MagicMock(
        side_effect=[
            event_payload(),
            {"events": [event_payload()], "total": 1, "offset": 0, "limit": 10},
            {"events": [event_payload()], "total": 1, "offset": 0, "limit": 10},
            {"events": [event_payload()], "total": 1, "offset": 0, "limit": 10},
            {"events": [event_payload()], "total": 1, "offset": 0, "limit": 10},
        ]
    )
    client.post = MagicMock(return_value=event_payload())

    assert client.events.get(1).id == 1
    assert client.events.list_by_product("prod-1")[0][0].id == 1
    assert client.events.list_by_product_and_type("prod-1", "CREATED")[0][0].id == 1
    assert client.events.get_all_for_product("prod-1")[0].id == 1

    created = client.events.create(NewTrackingEvent(**{
        "product_id": "prod-1",
        "actor_address": "actor-1",
        "timestamp": datetime.now(timezone.utc),
        "event_type": "CREATED",
        "location": "Warehouse",
        "data_hash": "hash",
        "note": "Created",
        "metadata": {},
    }))
    filtered = client.events.get_by_type_for_product("prod-1", "CREATED")

    assert created.id == 1
    assert filtered[0].event_type == "CREATED"


def test_stats_health_variants_are_mapped():
    client = build_client()
    now = datetime.now(timezone.utc).isoformat()
    client.get = MagicMock(
        side_effect=[
            {
                "status": "healthy",
                "service": "chainlogistics-backend",
                "timestamp": now,
                "checks": [{"name": "database", "status": "healthy", "latency_ms": 2}],
                "monitoring": {"error_rate": 0.0, "total_errors": 0},
            },
            {
                "status": "healthy",
                "service": "chainlogistics-backend",
                "timestamp": now,
                "checks": [{"name": "database", "status": "healthy", "latency_ms": 2}],
            },
            {
                "status": "healthy",
                "service": "chainlogistics-backend",
                "timestamp": now,
                "uptime_hint": "process accepting requests",
            },
            {
                "name": "database",
                "status": "healthy",
                "latency_ms": 1,
                "details": "postgres connection ok",
            },
            {
                "status": "healthy",
                "service": "chainlogistics-backend",
                "timestamp": now,
                "monitoring": {"error_rate": 1.0, "total_errors": 2, "top_errors": []},
            },
        ]
    )

    health = client.stats.health()
    readiness = client.stats.readiness()
    liveness = client.stats.liveness()
    db = client.stats.db_health()
    monitoring = client.stats.monitoring_health()

    assert health.monitoring.total_errors == 0
    assert readiness.checks[0].name == "database"
    assert liveness.uptime_hint == "process accepting requests"
    assert db.name == "database"
    assert monitoring.monitoring["total_errors"] == 2


def test_stats_global_maps_response():
    client = build_client()
    client.get = MagicMock(
        return_value={
            "total_products": 2,
            "active_products": 1,
            "total_events": 3,
            "total_users": 4,
            "active_api_keys": 5,
        }
    )

    stats = client.stats.get_global()

    assert stats.total_products == 2
