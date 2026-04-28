from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from chainlogistics_sdk.client import ChainLogisticsClient
from chainlogistics_sdk.config import Config
from chainlogistics_sdk.exceptions import (
    ApiError,
    AuthenticationError,
    ChainLogisticsError,
    ConfigError,
    NetworkError,
    TimeoutError,
    ValidationError,
)


def build_client() -> ChainLogisticsClient:
    return ChainLogisticsClient(
        Config("test-key", base_url="https://example.com").with_cache(ttl_seconds=60)
    )


def test_get_requests_use_cache():
    client = build_client()
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "chainlogistics-backend",
    }

    client.session.request = MagicMock(return_value=response)

    first = client.get("health")
    second = client.get("health")

    assert first["status"] == "healthy"
    assert second["service"] == "chainlogistics-backend"
    assert client.session.request.call_count == 1


def test_batch_get_returns_results_for_each_path():
    client = build_client()
    client.get = MagicMock(side_effect=[{"status": "healthy"}, {"status": "ready"}])

    result = client.batch_get([("health/live", None), ("health/ready", None)], max_workers=2)

    assert result["health/live"]["status"] == "healthy"
    assert result["health/ready"]["status"] == "ready"


def test_handle_response_maps_authentication_errors():
    client = build_client()
    response = MagicMock()
    response.raise_for_status.side_effect = __import__("requests").exceptions.HTTPError()
    response.status_code = 401
    response.json.return_value = {"error": "bad token"}
    response.text = "bad token"

    with pytest.raises(AuthenticationError):
        client._handle_response(response)


def test_handle_response_returns_plain_text_when_json_is_invalid():
    client = build_client()
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.side_effect = ValueError("invalid")
    response.text = "plain-text"

    assert client._handle_response(response) == "plain-text"


def test_handle_response_raises_api_error_when_json_and_text_missing():
    client = build_client()
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.side_effect = ValueError("invalid")
    response.text = ""

    with pytest.raises(ApiError):
        client._handle_response(response)


def test_request_maps_timeout_and_connection_errors():
    client = build_client()
    client.session.request = MagicMock(side_effect=__import__("requests").exceptions.Timeout("slow"))

    with pytest.raises(TimeoutError):
        client.get("health")

    client.session.request = MagicMock(
        side_effect=__import__("requests").exceptions.ConnectionError("down")
    )

    with pytest.raises(NetworkError):
        client.get("health")


def test_http_method_wrappers_delegate_to_request():
    client = build_client()
    client._request = MagicMock(return_value={"ok": True})

    assert client.post("health") == {"ok": True}
    assert client.put("health") == {"ok": True}
    assert client.delete("health") == {"ok": True}


def test_health_wrapper_methods_map_models():
    client = build_client()
    now = datetime.now(timezone.utc).isoformat()
    client.get = MagicMock(
        side_effect=[
            {"status": "healthy", "service": "svc", "timestamp": now, "checks": [], "monitoring": {"error_rate": 0.0, "total_errors": 0}},
            {"status": "healthy", "service": "svc", "timestamp": now, "checks": []},
            {"status": "healthy", "service": "svc", "timestamp": now, "uptime_hint": "up"},
            {"status": "healthy", "service": "svc", "timestamp": now, "monitoring": {"error_rate": 0.1, "total_errors": 1}},
            {"name": "database", "status": "healthy", "latency_ms": 1, "details": "ok"},
        ]
    )

    assert client.health_check().service == "svc"
    assert client.readiness_check().status == "healthy"
    assert client.liveness_check().uptime_hint == "up"
    assert client.monitoring_health().monitoring["total_errors"] == 1
    assert client.db_health_check().name == "database"


def test_context_manager_closes_session():
    client = build_client()
    client.session.close = MagicMock()

    with client as active_client:
        assert active_client is client

    client.session.close.assert_called_once()


def test_events_list_requires_product_id():
    client = build_client()

    with pytest.raises(ValidationError):
        client.events.list()


def test_clear_cache_resets_memory_cache():
    client = build_client()
    client.cache.set("GET:health:", {"status": "healthy"})

    client.clear_cache()

    assert client.cache.get("GET:health:") is None


def test_error_helpers_expose_retryability_and_status_checks():
    error = ChainLogisticsError("boom", status_code=503)
    rate_limit = ApiError("retry", status_code=503)

    assert error.is_server_error() is True
    assert error.is_client_error() is False
    assert rate_limit.is_retryable() is True

    assert str(ConfigError("bad config")) == "bad config"
