"""Configuration for the ChainLogistics SDK."""

from typing import Optional
from urllib.parse import urlparse

from .exceptions import ConfigError


class Config:
    """Configuration for the ChainLogistics client."""
    
    DEFAULT_BASE_URL = "https://api.chainlogistics.io"
    DEFAULT_TIMEOUT = 30
    DEFAULT_USER_AGENT = "chainlogistics-sdk-python/1.0.0"
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        user_agent: Optional[str] = None,
        enable_cache: bool = True,
        cache_ttl_seconds: int = 30,
        cache_max_entries: int = 256,
    ):
        """Initialize configuration.
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for the API (defaults to https://api.chainlogistics.io)
            timeout: Request timeout in seconds (defaults to 30)
            user_agent: Custom user agent string
        """
        self.api_key = api_key
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.enable_cache = enable_cache
        self.cache_ttl_seconds = cache_ttl_seconds
        self.cache_max_entries = cache_max_entries
        
        # Validate configuration
        self.validate()
    
    def validate(self) -> None:
        """Validate the configuration."""
        if not self.api_key:
            raise ConfigError("API key cannot be empty")
        
        if not self.base_url:
            raise ConfigError("Base URL cannot be empty")
        
        # Validate URL format
        try:
            parsed = urlparse(self.base_url)
            if not parsed.scheme or not parsed.netloc:
                raise ConfigError(f"Invalid base URL: {self.base_url}")
        except Exception as e:
            raise ConfigError(f"Invalid base URL: {e}")
        
        if self.timeout <= 0:
            raise ConfigError("Timeout must be greater than 0")

        if self.cache_ttl_seconds < 0:
            raise ConfigError("Cache TTL must be greater than or equal to 0")

        if self.cache_max_entries < 0:
            raise ConfigError("Cache max entries must be greater than or equal to 0")
    
    def with_base_url(self, base_url: str) -> "Config":
        """Return a new config with a different base URL."""
        return Config(
            api_key=self.api_key,
            base_url=base_url,
            timeout=self.timeout,
            user_agent=self.user_agent,
            enable_cache=self.enable_cache,
            cache_ttl_seconds=self.cache_ttl_seconds,
            cache_max_entries=self.cache_max_entries,
        )
    
    def with_timeout(self, timeout: int) -> "Config":
        """Return a new config with a different timeout."""
        return Config(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout,
            user_agent=self.user_agent,
            enable_cache=self.enable_cache,
            cache_ttl_seconds=self.cache_ttl_seconds,
            cache_max_entries=self.cache_max_entries,
        )
    
    def with_user_agent(self, user_agent: str) -> "Config":
        """Return a new config with a different user agent."""
        return Config(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            user_agent=user_agent,
            enable_cache=self.enable_cache,
            cache_ttl_seconds=self.cache_ttl_seconds,
            cache_max_entries=self.cache_max_entries,
        )

    def with_cache(self, ttl_seconds: int = 30, max_entries: int = 256) -> "Config":
        """Return a new config with in-memory caching enabled."""
        return Config(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            user_agent=self.user_agent,
            enable_cache=True,
            cache_ttl_seconds=ttl_seconds,
            cache_max_entries=max_entries,
        )

    def without_cache(self) -> "Config":
        """Return a new config with caching disabled."""
        return Config(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            user_agent=self.user_agent,
            enable_cache=False,
            cache_ttl_seconds=0,
            cache_max_entries=0,
        )
    
    def __repr__(self) -> str:
        return (
            f"Config(api_key=***REDACTED***, base_url={self.base_url}, "
            f"timeout={self.timeout}, user_agent={self.user_agent}, "
            f"enable_cache={self.enable_cache})"
        )
