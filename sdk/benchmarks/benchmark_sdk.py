"""Simple benchmark smoke tests for SDK client-side operations."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
import sys
from unittest.mock import MagicMock

PYTHON_SDK_SRC = Path(__file__).resolve().parents[1] / "python" / "src"
if str(PYTHON_SDK_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SDK_SRC))

from chainlogistics_sdk import ChainLogisticsClient, Config


def build_client() -> ChainLogisticsClient:
    client = ChainLogisticsClient(
        Config("benchmark-key", base_url="https://example.com").with_cache(ttl_seconds=60)
    )
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "status": "healthy",
        "service": "chainlogistics-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    client.session.request = MagicMock(return_value=response)
    return client


def benchmark_cached_health_check(iterations: int = 500) -> float:
    client = build_client()
    start = time.perf_counter()
    for _ in range(iterations):
        client.health_check()
    elapsed = time.perf_counter() - start
    print(f"cached_health_check_iterations={iterations}")
    print(f"cached_health_check_elapsed_seconds={elapsed:.6f}")
    print(f"http_calls={client.session.request.call_count}")
    return elapsed


if __name__ == "__main__":
    elapsed = benchmark_cached_health_check()
    if elapsed <= 0:
        raise SystemExit("benchmark did not execute correctly")
