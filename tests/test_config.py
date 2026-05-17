"""Tests for FlightFinder configuration."""

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from flightfinder.config import APIConfig, CacheConfig, Config, SearchDefaults


class TestAPIConfig:
    """Tests for APIConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = APIConfig()
        assert config.base_url == "https://api.skypicker.com/umbrella/v2/graphql"
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.retry_backoff == 2.0


class TestCacheConfig:
    """Tests for CacheConfig."""

    def test_default_values(self):
        """Test default cache configuration."""
        config = CacheConfig()
        assert config.enabled is True
        assert config.ttl_seconds == 300
        assert config.max_size == 100


class TestSearchDefaults:
    """Tests for SearchDefaults."""

    def test_default_values(self):
        """Test default search parameters."""
        config = SearchDefaults()
        assert config.adults == 1
        assert config.cabin_class == "ECONOMY"
        assert config.max_stops == 2
        assert config.sort_by == "PRICE"


class TestConfig:
    """Tests for main Config class."""

    def test_default_config(self):
        """Test default configuration."""
        config = Config()
        assert config.api is not None
        assert config.cache is not None
        assert config.search_defaults is not None

    def test_from_file(self):
        """Test loading config from file."""
        config_data = {
            "api": {
                "timeout": 60.0,
                "max_retries": 5,
            },
            "cache": {
                "enabled": False,
                "ttl_seconds": 600,
            },
            "search_defaults": {
                "cabin_class": "BUSINESS",
                "max_stops": 1,
            },
        }

        with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            config = Config.from_file(temp_path)
            assert config.api.timeout == 60.0
            assert config.api.max_retries == 5
            assert config.cache.enabled is False
            assert config.cache.ttl_seconds == 600
            assert config.search_defaults.cabin_class == "BUSINESS"
            assert config.search_defaults.max_stops == 1
        finally:
            os.unlink(temp_path)

    def test_from_file_missing(self):
        """Test loading from non-existent file returns defaults."""
        config = Config.from_file("/nonexistent/path/config.json")
        assert config.api.timeout == 30.0  # Default value

    def test_from_env(self):
        """Test loading config from environment variables."""
        env_vars = {
            "FLIGHTFINDER_API_URL": "https://custom.api.com",
            "FLIGHTFINDER_TIMEOUT": "45.0",
            "FLIGHTFINDER_MAX_RETRIES": "5",
            "FLIGHTFINDER_CACHE_ENABLED": "false",
            "FLIGHTFINDER_CACHE_TTL": "600",
        }

        # Set environment variables
        for key, value in env_vars.items():
            os.environ[key] = value

        try:
            config = Config.from_env()
            assert config.api.base_url == "https://custom.api.com"
            assert config.api.timeout == 45.0
            assert config.api.max_retries == 5
            assert config.cache.enabled is False
            assert config.cache.ttl_seconds == 600
        finally:
            # Clean up environment
            for key in env_vars:
                del os.environ[key]

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = Config()
        data = config.to_dict()

        assert "api" in data
        assert "cache" in data
        assert "search_defaults" in data
        assert data["api"]["timeout"] == 30.0
        assert data["cache"]["enabled"] is True

    def test_save(self):
        """Test saving config to file."""
        config = Config()
        config.api.timeout = 45.0
        config.cache.ttl_seconds = 600

        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "test_config.json"
            config.save(path)

            # Verify file was created
            assert path.exists()

            # Verify content
            with open(path) as f:
                data = json.load(f)
            assert data["api"]["timeout"] == 45.0
            assert data["cache"]["ttl_seconds"] == 600

    def test_load_priority(self):
        """Test configuration loading priority."""
        # Create config file
        config_data = {"api": {"timeout": 99.0}}

        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "flightfinder.json"
            with open(config_path, "w") as f:
                json.dump(config_data, f)

            # Set env var pointing to config
            os.environ["FLIGHTFINDER_CONFIG"] = str(config_path)

            try:
                config = Config.load()
                assert config.api.timeout == 99.0
            finally:
                del os.environ["FLIGHTFINDER_CONFIG"]
