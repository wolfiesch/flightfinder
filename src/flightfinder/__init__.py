"""FlightFinder - Python client for Kiwi/Skypicker flight search API."""

from flightfinder.client import FlightFinder
from flightfinder.async_client import AsyncFlightFinder
from flightfinder.models import Flight, Location, Itinerary, RoundTrip, Segment
from flightfinder.config import Config, get_config, set_config
from flightfinder.cache import ResponseCache, get_cache, clear_cache
from flightfinder.exceptions import (
    FlightFinderError,
    APIError,
    RateLimitError,
    ValidationError,
    NetworkError,
    TimeoutError,
    ParseError,
    ConfigurationError,
)

__all__ = [
    # Clients
    "FlightFinder",
    "AsyncFlightFinder",
    # Models
    "Flight",
    "Location",
    "Itinerary",
    "RoundTrip",
    "Segment",
    # Configuration
    "Config",
    "get_config",
    "set_config",
    # Cache
    "ResponseCache",
    "get_cache",
    "clear_cache",
    # Exceptions
    "FlightFinderError",
    "APIError",
    "RateLimitError",
    "ValidationError",
    "NetworkError",
    "TimeoutError",
    "ParseError",
    "ConfigurationError",
]
__version__ = "0.2.0"
