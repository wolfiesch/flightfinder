"""Tests for HotelFinder client."""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from flightfinder.hotel_client import HotelFinder
from flightfinder.hotel_models import (
    Hotel,
    HotelRate,
    HotelRates,
    HotelSearchResults,
    HotelLocation,
    HotelPriceRange,
    HotelReviewSummary,
    get_location_key,
    parse_location_key_from_url,
    LOCATION_KEYS,
)
from flightfinder.exceptions import ValidationError, APIError


class TestLocationKeyHelpers:
    """Tests for location key helper functions."""

    def test_get_location_key_known_city(self):
        """Should return location key for known cities."""
        assert get_location_key("new york") == "g60763"
        assert get_location_key("New York") == "g60763"
        assert get_location_key("NYC") == "g60763"
        assert get_location_key("tokyo") == "g298184"

    def test_get_location_key_unknown_city(self):
        """Should return None for unknown cities."""
        assert get_location_key("unknownville") is None
        assert get_location_key("") is None

    def test_parse_location_key_from_url(self):
        """Should extract location key from TripAdvisor URLs."""
        url = "https://www.tripadvisor.com/Hotels-g60763-New_York_City-Hotels.html"
        assert parse_location_key_from_url(url) == "g60763"

        url = "https://www.tripadvisor.com/Hotels-g298184-Tokyo-Hotels.html"
        assert parse_location_key_from_url(url) == "g298184"

    def test_parse_location_key_invalid_url(self):
        """Should return None for invalid URLs."""
        assert parse_location_key_from_url("not a url") is None
        assert parse_location_key_from_url("https://example.com") is None

    def test_location_keys_coverage(self):
        """Verify location keys dictionary has expected entries."""
        assert len(LOCATION_KEYS) > 50
        assert "new york" in LOCATION_KEYS
        assert "paris" in LOCATION_KEYS
        assert "tokyo" in LOCATION_KEYS


class TestHotelModels:
    """Tests for hotel data models."""

    def test_hotel_price_range(self):
        """Test HotelPriceRange model."""
        price_range = HotelPriceRange(minimum=100, maximum=500)
        assert price_range.midpoint == 300
        assert str(price_range) == "$100-$500"

    def test_hotel_review_summary(self):
        """Test HotelReviewSummary model."""
        review = HotelReviewSummary(rating=4.7, count=1500)
        assert review.rating_label == "Excellent"

        review = HotelReviewSummary(rating=4.2, count=100)
        assert review.rating_label == "Very Good"

        review = HotelReviewSummary(rating=3.0, count=50)
        assert review.rating_label == "Average"

    def test_hotel_model(self):
        """Test Hotel model with all fields."""
        hotel = Hotel(
            key="g60763-d12345",
            name="Test Hotel",
            accommodation_type="Hotel",
            review_summary=HotelReviewSummary(rating=4.5, count=100),
            price_range=HotelPriceRange(minimum=150, maximum=300),
            location=HotelLocation(latitude=40.7, longitude=-74.0),
            mentions=["Modern", "Business"],
            labels=["Best seller"],
        )

        assert hotel.rating == 4.5
        assert hotel.review_count == 100
        assert hotel.min_price == 150
        assert hotel.max_price == 300
        assert hotel.tripadvisor_id == "12345"
        assert hotel.location_id == "g60763"

    def test_hotel_rates_model(self):
        """Test HotelRates model."""
        rates = HotelRates(
            hotel_key="g60763-d12345",
            check_in=date(2025, 3, 1),
            check_out=date(2025, 3, 3),
            rates=[
                HotelRate(provider="Booking.com", price=250),
                HotelRate(provider="Expedia", price=220),
            ],
        )

        assert rates.nights == 2
        assert rates.cheapest.provider == "Expedia"
        assert rates.cheapest_price == 220
        assert rates.price_per_night == 110

    def test_hotel_search_results(self):
        """Test HotelSearchResults model."""
        results = HotelSearchResults(
            location_key="g60763",
            total_count=1000,
            hotels=[Hotel(key="test", name="Test", accommodation_type="Hotel")],
            offset=0,
            limit=30,
        )

        assert results.has_more is True

        results.total_count = 1
        assert results.has_more is False


class TestHotelFinder:
    """Tests for HotelFinder client."""

    def test_init_with_defaults(self):
        """Should initialize with default settings."""
        finder = HotelFinder()
        assert finder.timeout == 30.0
        assert finder.max_retries == 3
        finder.close()

    def test_init_with_custom_settings(self):
        """Should accept custom settings."""
        finder = HotelFinder(timeout=60.0, max_retries=5, cache_enabled=False)
        assert finder.timeout == 60.0
        assert finder.max_retries == 5
        assert finder._cache is None
        finder.close()

    def test_context_manager(self):
        """Should work as context manager."""
        with HotelFinder() as finder:
            assert finder._client is None  # Lazy initialization
            _ = finder.client
            assert finder._client is not None
        assert finder._client is None  # Closed after exit

    def test_search_hotels_empty_location_raises(self):
        """Should raise ValidationError for empty location."""
        with HotelFinder() as finder:
            with pytest.raises(ValidationError) as exc_info:
                finder.search_hotels("")
            assert "empty" in str(exc_info.value).lower()

    def test_search_hotels_unknown_location_raises(self):
        """Should raise ValidationError for unknown location."""
        with HotelFinder() as finder:
            with pytest.raises(ValidationError) as exc_info:
                finder.search_hotels("unknownville123")
            assert "Unknown location" in str(exc_info.value)

    def test_get_hotel_rates_invalid_dates(self):
        """Should raise ValidationError for invalid date range."""
        with HotelFinder() as finder:
            with pytest.raises(ValidationError) as exc_info:
                finder.get_hotel_rates(
                    hotel_key="g60763-d12345",
                    check_in=date(2025, 3, 5),
                    check_out=date(2025, 3, 1),  # Before check-in
                )
            assert "Check-out" in str(exc_info.value)

    def test_get_hotel_rates_past_date(self):
        """Should raise ValidationError for past check-in date."""
        with HotelFinder() as finder:
            with pytest.raises(ValidationError) as exc_info:
                finder.get_hotel_rates(
                    hotel_key="g60763-d12345",
                    check_in=date(2020, 1, 1),
                    check_out=date(2020, 1, 3),
                )
            assert "past" in str(exc_info.value).lower()


class TestHotelFinderIntegration:
    """Integration tests for HotelFinder (requires network)."""

    @pytest.mark.integration
    def test_search_hotels_nyc(self):
        """Should return hotels for NYC."""
        with HotelFinder() as finder:
            results = finder.search_hotels("new york", limit=5)

            assert results.location_key == "g60763"
            assert results.total_count > 0
            assert len(results.hotels) > 0
            assert len(results.hotels) <= 5

            hotel = results.hotels[0]
            assert hotel.key.startswith("g60763")
            assert hotel.name
            assert hotel.accommodation_type

    @pytest.mark.integration
    def test_search_hotels_with_filters(self):
        """Should apply client-side filters."""
        with HotelFinder() as finder:
            results = finder.search_hotels(
                "nyc",
                limit=30,
                min_price=200,
                max_price=400,
                min_rating=4.0,
            )

            for hotel in results.hotels:
                if hotel.min_price:
                    assert hotel.min_price >= 200 or hotel.max_price >= 200
                if hotel.rating:
                    assert hotel.rating >= 4.0

    @pytest.mark.integration
    def test_search_hotels_by_location_key(self):
        """Should accept location key directly."""
        with HotelFinder() as finder:
            results = finder.search_hotels("g60763", limit=3)

            assert results.location_key == "g60763"
            assert len(results.hotels) > 0

    @pytest.mark.integration
    def test_cache_behavior(self):
        """Should cache responses."""
        with HotelFinder(cache_enabled=True) as finder:
            # First request
            results1 = finder.search_hotels("sf", limit=5)

            # Second request should hit cache
            results2 = finder.search_hotels("sf", limit=5)

            # Results should be identical
            assert len(results1.hotels) == len(results2.hotels)
            assert results1.hotels[0].key == results2.hotels[0].key

            # Check cache stats
            stats = finder.cache_stats()
            assert stats is not None
            assert stats.get("hits", 0) > 0
