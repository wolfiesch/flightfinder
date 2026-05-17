"""Configuration management for FlightFinder."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class APIConfig:
    """API configuration settings."""

    base_url: str = "https://api.skypicker.com/umbrella/v2/graphql"
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    user_agent: str = "FlightFinder/0.1.0"


@dataclass
class CacheConfig:
    """Cache configuration settings."""

    enabled: bool = True
    ttl_seconds: int = 300  # 5 minutes
    max_size: int = 100  # Maximum number of cached responses


@dataclass
class SearchDefaults:
    """Default search parameters."""

    adults: int = 1
    children: int = 0
    infants: int = 0
    cabin_class: str = "ECONOMY"
    max_stops: int = 2
    sort_by: str = "PRICE"
    limit: int = 100
    currency: str = "usd"
    locale: str = "en"
    content_providers: list[str] = field(default_factory=lambda: ["KIWI", "FRESH", "KAYAK"])


@dataclass
class DiscordConfig:
    """Discord webhook notification settings."""

    webhook_url: str = ""
    enabled: bool = True
    verbose_level: str = "ultra"  # minimal, normal, verbose, ultra
    send_search_results: bool = True
    send_deal_alerts: bool = True
    send_monitoring_status: bool = True
    rate_limit_delay: float = 0.5


@dataclass
class MonitorConfig:
    """Background monitoring settings."""

    interval_seconds: int = 300  # 5 minutes
    days_ahead: int = 30
    search_window: int = 14
    heartbeat_interval: int = 3600  # 1 hour


@dataclass
class Config:
    """Main configuration container."""

    api: APIConfig = field(default_factory=APIConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    search_defaults: SearchDefaults = field(default_factory=SearchDefaults)
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)

    @classmethod
    def from_file(cls, path: str | Path) -> "Config":
        """Load configuration from a JSON file."""
        path = Path(path)
        if not path.exists():
            return cls()

        with open(path) as f:
            data = json.load(f)

        return cls._from_dict(data)

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        config = cls()

        # API config from env
        if url := os.getenv("FLIGHTFINDER_API_URL"):
            config.api.base_url = url
        if timeout := os.getenv("FLIGHTFINDER_TIMEOUT"):
            config.api.timeout = float(timeout)
        if retries := os.getenv("FLIGHTFINDER_MAX_RETRIES"):
            config.api.max_retries = int(retries)

        # Cache config from env
        if cache_enabled := os.getenv("FLIGHTFINDER_CACHE_ENABLED"):
            config.cache.enabled = cache_enabled.lower() in ("true", "1", "yes")
        if cache_ttl := os.getenv("FLIGHTFINDER_CACHE_TTL"):
            config.cache.ttl_seconds = int(cache_ttl)

        # Discord config from env
        if webhook_url := os.getenv("DISCORD_WEBHOOK_URL"):
            config.discord.webhook_url = webhook_url
        if discord_enabled := os.getenv("DISCORD_ENABLED"):
            config.discord.enabled = discord_enabled.lower() in ("true", "1", "yes")
        if verbose_level := os.getenv("DISCORD_VERBOSE_LEVEL"):
            config.discord.verbose_level = verbose_level

        # Monitor config from env
        if interval := os.getenv("MONITOR_INTERVAL"):
            config.monitor.interval_seconds = int(interval)
        if days_ahead := os.getenv("MONITOR_DAYS_AHEAD"):
            config.monitor.days_ahead = int(days_ahead)

        return config

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> "Config":
        """
        Load configuration from file or environment.

        Priority:
        1. Explicit config_path if provided
        2. FLIGHTFINDER_CONFIG env var
        3. ~/.flightfinder/config.json
        4. ./flightfinder.json
        5. Environment variables
        6. Defaults
        """
        # Check explicit path
        if config_path:
            return cls.from_file(config_path)

        # Check env var for config path
        if env_path := os.getenv("FLIGHTFINDER_CONFIG"):
            return cls.from_file(env_path)

        # Check standard locations
        standard_paths = [
            Path.home() / ".flightfinder" / "config.json",
            Path("flightfinder.json"),
        ]

        for path in standard_paths:
            if path.exists():
                return cls.from_file(path)

        # Fall back to environment variables
        return cls.from_env()

    @classmethod
    def _from_dict(cls, data: dict) -> "Config":
        """Create config from dictionary."""
        config = cls()

        if api_data := data.get("api"):
            for key, value in api_data.items():
                if hasattr(config.api, key):
                    setattr(config.api, key, value)

        if cache_data := data.get("cache"):
            for key, value in cache_data.items():
                if hasattr(config.cache, key):
                    setattr(config.cache, key, value)

        if search_data := data.get("search_defaults"):
            for key, value in search_data.items():
                if hasattr(config.search_defaults, key):
                    setattr(config.search_defaults, key, value)

        if discord_data := data.get("discord"):
            for key, value in discord_data.items():
                if hasattr(config.discord, key):
                    setattr(config.discord, key, value)

        if monitor_data := data.get("monitor"):
            for key, value in monitor_data.items():
                if hasattr(config.monitor, key):
                    setattr(config.monitor, key, value)

        return config

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "api": {
                "base_url": self.api.base_url,
                "timeout": self.api.timeout,
                "max_retries": self.api.max_retries,
                "retry_delay": self.api.retry_delay,
                "retry_backoff": self.api.retry_backoff,
                "user_agent": self.api.user_agent,
            },
            "cache": {
                "enabled": self.cache.enabled,
                "ttl_seconds": self.cache.ttl_seconds,
                "max_size": self.cache.max_size,
            },
            "search_defaults": {
                "adults": self.search_defaults.adults,
                "children": self.search_defaults.children,
                "infants": self.search_defaults.infants,
                "cabin_class": self.search_defaults.cabin_class,
                "max_stops": self.search_defaults.max_stops,
                "sort_by": self.search_defaults.sort_by,
                "limit": self.search_defaults.limit,
                "currency": self.search_defaults.currency,
                "locale": self.search_defaults.locale,
                "content_providers": self.search_defaults.content_providers,
            },
            "discord": {
                "webhook_url": self.discord.webhook_url,
                "enabled": self.discord.enabled,
                "verbose_level": self.discord.verbose_level,
                "send_search_results": self.discord.send_search_results,
                "send_deal_alerts": self.discord.send_deal_alerts,
                "send_monitoring_status": self.discord.send_monitoring_status,
                "rate_limit_delay": self.discord.rate_limit_delay,
            },
            "monitor": {
                "interval_seconds": self.monitor.interval_seconds,
                "days_ahead": self.monitor.days_ahead,
                "search_window": self.monitor.search_window,
                "heartbeat_interval": self.monitor.heartbeat_interval,
            },
        }

    def save(self, path: str | Path) -> None:
        """Save configuration to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


# Global default configuration
_default_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _default_config
    if _default_config is None:
        _default_config = Config.load()
    return _default_config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _default_config
    _default_config = config
