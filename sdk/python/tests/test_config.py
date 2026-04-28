import pytest

from chainlogistics_sdk.config import Config
from chainlogistics_sdk.exceptions import ConfigError


def test_with_cache_updates_cache_settings():
    config = Config("test-key").with_cache(ttl_seconds=120, max_entries=32)

    assert config.enable_cache is True
    assert config.cache_ttl_seconds == 120
    assert config.cache_max_entries == 32


def test_without_cache_disables_caching():
    config = Config("test-key").without_cache()

    assert config.enable_cache is False
    assert config.cache_ttl_seconds == 0
    assert config.cache_max_entries == 0


def test_builder_helpers_preserve_other_fields():
    config = (
        Config("test-key")
        .with_base_url("https://api.example.com")
        .with_timeout(99)
        .with_user_agent("custom-agent")
    )

    assert config.base_url == "https://api.example.com"
    assert config.timeout == 99
    assert config.user_agent == "custom-agent"


def test_repr_redacts_api_key():
    config = Config("secret-key")

    rendered = repr(config)

    assert "secret-key" not in rendered
    assert "***REDACTED***" in rendered


@pytest.mark.parametrize(
    ("ttl", "max_entries"),
    [(-1, 10), (30, -2)],
)
def test_invalid_cache_configuration_raises(ttl, max_entries):
    with pytest.raises(ConfigError):
        Config(
            "test-key",
            cache_ttl_seconds=ttl,
            cache_max_entries=max_entries,
        )
