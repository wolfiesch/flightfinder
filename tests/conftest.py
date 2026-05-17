"""Pytest fixtures for FlightFinder tests."""

from datetime import datetime

import pytest

from flightfinder.cache import ResponseCache
from flightfinder.client import FlightFinder
from flightfinder.config import Config
from flightfinder.models import Flight, Location, Segment


@pytest.fixture
def mock_config():
    """Create a test configuration."""
    config = Config()
    config.api.timeout = 5.0
    config.api.max_retries = 1
    config.cache.enabled = False
    return config


@pytest.fixture
def mock_cache():
    """Create a test cache."""
    return ResponseCache(max_size=10, default_ttl=60)


@pytest.fixture
def client(mock_config):
    """Create a FlightFinder client with test config."""
    return FlightFinder(config=mock_config, cache=None)


@pytest.fixture
def sample_location_response():
    """Sample API response for location search."""
    return {
        "data": {
            "places": {
                "__typename": "PlaceConnection",
                "edges": [
                    {
                        "node": {
                            "__typename": "Station",
                            "id": "airport_1",
                            "legacyId": "SFO",
                            "name": "San Francisco International",
                            "slug": "san-francisco-sfo",
                            "type": "AIRPORT",
                            "gps": {"lat": 37.619, "lng": -122.374},
                            "city": {
                                "name": "San Francisco",
                                "country": {"name": "United States", "code": "US"},
                            },
                        }
                    },
                    {
                        "node": {
                            "__typename": "City",
                            "id": "city_1",
                            "legacyId": "san-francisco_ca_us",
                            "name": "San Francisco",
                            "slug": "san-francisco",
                            "code": "SFO",
                            "gps": {"lat": 37.7749, "lng": -122.4194},
                            "country": {"name": "United States", "code": "US"},
                        }
                    },
                ],
            }
        }
    }


@pytest.fixture
def sample_flight_response():
    """Sample API response for one-way flight search."""
    return {
        "data": {
            "onewayItineraries": {
                "__typename": "Itineraries",
                "itineraries": [
                    {
                        "__typename": "ItineraryOneWay",
                        "id": "flight_1",
                        "price": {"amount": "150.00"},
                        "priceEur": {"amount": "140.00"},
                        "sector": {
                            "duration": 7200,
                            "sectorSegments": [
                                {
                                    "segment": {
                                        "source": {
                                            "station": {"code": "SFO", "name": "San Francisco"},
                                            "localTime": "2025-02-15T08:00:00",
                                        },
                                        "destination": {
                                            "station": {"code": "LAX", "name": "Los Angeles"},
                                            "localTime": "2025-02-15T10:00:00",
                                        },
                                        "duration": 7200,
                                        "carrier": {"code": "UA", "name": "United Airlines"},
                                    }
                                }
                            ],
                        },
                        "bookingOptions": {
                            "edges": [{"node": {"bookingUrl": "https://booking.example.com/1"}}]
                        },
                    },
                    {
                        "__typename": "ItineraryOneWay",
                        "id": "flight_2",
                        "price": {"amount": "200.00"},
                        "priceEur": {"amount": "185.00"},
                        "sector": {
                            "duration": 12600,
                            "sectorSegments": [
                                {
                                    "segment": {
                                        "source": {
                                            "station": {"code": "SFO", "name": "San Francisco"},
                                            "localTime": "2025-02-15T06:00:00",
                                        },
                                        "destination": {
                                            "station": {"code": "DEN", "name": "Denver"},
                                            "localTime": "2025-02-15T09:30:00",
                                        },
                                        "duration": 8100,
                                        "carrier": {"code": "UA", "name": "United Airlines"},
                                    }
                                },
                                {
                                    "segment": {
                                        "source": {
                                            "station": {"code": "DEN", "name": "Denver"},
                                            "localTime": "2025-02-15T10:30:00",
                                        },
                                        "destination": {
                                            "station": {"code": "LAX", "name": "Los Angeles"},
                                            "localTime": "2025-02-15T12:00:00",
                                        },
                                        "duration": 5400,
                                        "carrier": {"code": "UA", "name": "United Airlines"},
                                    }
                                },
                            ],
                        },
                        "bookingOptions": {
                            "edges": [{"node": {"bookingUrl": "https://booking.example.com/2"}}]
                        },
                    },
                ],
            }
        }
    }


@pytest.fixture
def sample_roundtrip_response():
    """Sample API response for round-trip flight search."""
    return {
        "data": {
            "returnItineraries": {
                "__typename": "Itineraries",
                "itineraries": [
                    {
                        "__typename": "ItineraryReturn",
                        "id": "rt_1",
                        "price": {"amount": "350.00"},
                        "bagsInfo": {
                            "includedCheckedBags": 0,
                            "checkedBagTiers": [{"tierPrice": {"amount": "35.00"}}],
                        },
                        "outbound": {
                            "duration": 7200,
                            "sectorSegments": [
                                {
                                    "segment": {
                                        "source": {
                                            "station": {"code": "SFO", "name": "San Francisco"},
                                            "localTime": "2025-02-15T08:00:00",
                                        },
                                        "destination": {
                                            "station": {
                                                "code": "LAX",
                                                "name": "Los Angeles",
                                                "city": {
                                                    "name": "Los Angeles",
                                                    "country": {
                                                        "code": "US",
                                                        "name": "United States",
                                                    },
                                                },
                                            },
                                            "localTime": "2025-02-15T10:00:00",
                                        },
                                        "duration": 7200,
                                        "carrier": {"code": "UA", "name": "United Airlines"},
                                    }
                                }
                            ],
                        },
                        "inbound": {
                            "duration": 7200,
                            "sectorSegments": [
                                {
                                    "segment": {
                                        "source": {
                                            "station": {"code": "LAX", "name": "Los Angeles"},
                                            "localTime": "2025-02-22T18:00:00",
                                        },
                                        "destination": {
                                            "station": {"code": "SFO", "name": "San Francisco"},
                                            "localTime": "2025-02-22T20:00:00",
                                        },
                                        "duration": 7200,
                                        "carrier": {"code": "UA", "name": "United Airlines"},
                                    }
                                }
                            ],
                        },
                        "bookingOptions": {
                            "edges": [{"node": {"bookingUrl": "https://booking.example.com/rt1"}}]
                        },
                    }
                ],
            }
        }
    }


@pytest.fixture
def sample_flight():
    """Create a sample Flight object."""
    segment = Segment(
        carrier="UA",
        carrier_name="United Airlines",
        departure_time=datetime(2025, 2, 15, 8, 0),
        arrival_time=datetime(2025, 2, 15, 10, 0),
        origin="SFO",
        origin_name="San Francisco",
        destination="LAX",
        destination_name="Los Angeles",
        duration_minutes=120,
        cabin_class="ECONOMY",
    )
    return Flight(
        id="test_flight",
        price=150.0,
        currency="USD",
        departure_time=datetime(2025, 2, 15, 8, 0),
        arrival_time=datetime(2025, 2, 15, 10, 0),
        origin="SFO",
        origin_city="San Francisco",
        destination="LAX",
        destination_city="Los Angeles",
        duration_minutes=120,
        stops=0,
        segments=[segment],
        deep_link="https://booking.example.com",
    )


@pytest.fixture
def sample_location():
    """Create a sample Location object."""
    return Location(
        id="SFO",
        name="San Francisco International",
        slug="san-francisco-sfo",
        type="AIRPORT",
        city="San Francisco",
        country="United States",
        country_code="US",
        latitude=37.619,
        longitude=-122.374,
    )
