"""Tests for FlightFinder client."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from flightfinder.client import FlightFinder
from flightfinder.exceptions import (
    APIError,
    NetworkError,
    RateLimitError,
    ValidationError,
)


class TestFlightFinderInit:
    """Tests for FlightFinder initialization."""

    def test_default_init(self):
        """Test default initialization."""
        finder = FlightFinder()
        assert finder.config is not None
        assert finder._client is None
        finder.close()

    def test_init_with_config(self, mock_config):
        """Test initialization with custom config."""
        finder = FlightFinder(config=mock_config)
        assert finder.config.api.timeout == 5.0
        finder.close()

    def test_init_with_legacy_timeout(self):
        """Test initialization with legacy timeout parameter."""
        finder = FlightFinder(timeout=10.0)
        assert finder.config.api.timeout == 10.0
        finder.close()

    def test_context_manager(self, mock_config):
        """Test context manager usage."""
        with FlightFinder(config=mock_config) as finder:
            assert finder is not None
        # Client should be closed after exiting context


class TestFindLocation:
    """Tests for location search."""

    def test_find_location_empty_term(self, client):
        """Test error on empty search term."""
        with pytest.raises(ValidationError) as exc_info:
            client.find_location("")
        assert exc_info.value.field == "term"

    def test_find_location_success(self, client, sample_location_response):
        """Test successful location search."""
        with patch.object(client, "_execute_query", return_value=sample_location_response):
            locations = client.find_location("San Francisco")

        assert len(locations) == 2
        assert locations[0].id == "SFO"
        assert locations[0].name == "San Francisco International"
        assert locations[0].type == "AIRPORT"
        assert locations[0].country_code == "US"

    def test_find_location_with_type_filter(self, client, sample_location_response):
        """Test location search with type filter."""
        with patch.object(client, "_execute_query", return_value=sample_location_response) as mock:
            client.find_location("San Francisco", location_types=["AIRPORT"])

        call_args = mock.call_args[0]
        variables = call_args[1]
        assert variables["filter"]["types"] == ["AIRPORT"]

    def test_find_location_api_error(self, client):
        """Test API error handling."""
        error_response = {
            "data": {
                "places": {
                    "__typename": "AppError",
                    "error": "Invalid query",
                }
            }
        }
        with patch.object(client, "_execute_query", return_value=error_response):
            with pytest.raises(APIError) as exc_info:
                client.find_location("test")
        assert "Invalid query" in str(exc_info.value)


class TestSearchFlights:
    """Tests for flight search."""

    def test_search_flights_empty_origin(self, client):
        """Test error on empty origin."""
        with pytest.raises(ValidationError) as exc_info:
            client.search_flights("")
        assert exc_info.value.field == "origin"

    def test_search_flights_success(self, client, sample_flight_response):
        """Test successful flight search."""
        with patch.object(client, "_execute_query", return_value=sample_flight_response):
            flights = client.search_flights(
                origin="SFO",
                destination="LAX",
                departure_from=date(2025, 2, 15),
            )

        assert len(flights) == 2
        assert flights[0].price == 150.0
        assert flights[0].origin == "SFO"
        assert flights[0].destination == "LAX"
        assert flights[0].stops == 0

        # Second flight has 1 stop
        assert flights[1].price == 200.0
        assert flights[1].stops == 1

    def test_search_flights_with_price_filter(self, client, sample_flight_response):
        """Test flight search with price filters."""
        with patch.object(client, "_execute_query", return_value=sample_flight_response) as mock:
            client.search_flights(
                origin="SFO",
                min_price=100,
                max_price=300,
            )

        call_args = mock.call_args[0]
        variables = call_args[1]
        assert variables["filter"]["price"]["start"] == 100
        assert variables["filter"]["price"]["end"] == 300

    def test_search_flights_api_error(self, client):
        """Test API error handling."""
        error_response = {
            "data": {
                "onewayItineraries": {
                    "__typename": "AppError",
                    "error": "Search failed",
                }
            }
        }
        with patch.object(client, "_execute_query", return_value=error_response):
            with pytest.raises(APIError):
                client.search_flights("SFO")

    def test_search_anywhere(self, client, sample_flight_response):
        """Test search_anywhere convenience method."""
        with patch.object(client, "_execute_query", return_value=sample_flight_response) as mock:
            client.search_anywhere("SFO")

        call_args = mock.call_args[0]
        variables = call_args[1]
        assert variables["search"]["itinerary"]["destination"]["ids"] == ["anywhere"]


class TestSearchRoundtrip:
    """Tests for round-trip search."""

    def test_search_roundtrip_empty_origin(self, client):
        """Test error on empty origin."""
        with pytest.raises(ValidationError) as exc_info:
            client.search_roundtrip("")
        assert exc_info.value.field == "origin"

    def test_search_roundtrip_invalid_days(self, client):
        """Test error on invalid min/max days."""
        with pytest.raises(ValidationError) as exc_info:
            client.search_roundtrip("SFO", min_days=0)
        assert exc_info.value.field == "min_days"

        with pytest.raises(ValidationError) as exc_info:
            client.search_roundtrip("SFO", min_days=14, max_days=7)
        assert exc_info.value.field == "max_days"

    def test_search_roundtrip_success(self, client, sample_roundtrip_response):
        """Test successful round-trip search."""
        with patch.object(client, "_execute_query", return_value=sample_roundtrip_response):
            roundtrips = client.search_roundtrip(
                origin="SFO",
                destination="LAX",
                departure_from=date(2025, 2, 15),
                min_days=7,
                max_days=14,
            )

        assert len(roundtrips) == 1
        rt = roundtrips[0]
        assert rt.price == 350.0
        assert rt.origin == "SFO"
        assert rt.destination == "LAX"
        assert rt.trip_days == 7
        assert rt.checked_bag_price == 35.0


class TestCaching:
    """Tests for response caching."""

    def test_caching_disabled(self, mock_config):
        """Test that caching can be disabled."""
        mock_config.cache.enabled = False
        finder = FlightFinder(config=mock_config)
        assert finder._cache is None
        finder.close()

    def test_cache_stats(self, mock_config, mock_cache):
        """Test cache statistics."""
        mock_config.cache.enabled = True
        finder = FlightFinder(config=mock_config, cache=mock_cache)
        stats = finder.cache_stats()
        assert stats is not None
        assert "hits" in stats
        assert "misses" in stats
        finder.close()

    def test_clear_cache(self, mock_config, mock_cache):
        """Test cache clearing."""
        mock_config.cache.enabled = True
        mock_cache.set("test", {"key": "value"}, {"data": "test"})
        finder = FlightFinder(config=mock_config, cache=mock_cache)
        cleared = finder.clear_cache()
        assert cleared >= 0
        finder.close()


class TestErrorHandling:
    """Tests for error handling and retry logic."""

    def test_network_error_retry(self, client):
        """Test that network errors trigger retries."""
        import httpx

        mock_http_client = MagicMock()
        mock_http_client.post.side_effect = httpx.ConnectError("Connection refused")

        # Inject the mock client
        client._client = mock_http_client

        with pytest.raises(NetworkError):
            client._execute_query("query", {})

    def test_rate_limit_error(self, client):
        """Test rate limit handling."""

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}

        mock_http_client = MagicMock()
        mock_http_client.post.return_value = mock_response

        # Inject the mock client
        client._client = mock_http_client

        with pytest.raises(RateLimitError) as exc_info:
            client._execute_query("query", {})
        assert exc_info.value.retry_after == 60
