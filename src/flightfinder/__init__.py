"""FlightFinder - Python client for Kiwi/Skypicker flight search API and Xotelo hotel search."""

from flightfinder.client import FlightFinder
from flightfinder.async_client import AsyncFlightFinder
from flightfinder.models import Flight, Location, Itinerary, RoundTrip, Segment
from flightfinder.hotel_client import HotelFinder
from flightfinder.hotel_models import (
    Hotel,
    HotelRate,
    HotelRates,
    HotelSearchResults,
    HotelLocation,
    HotelPriceRange,
    HotelReviewSummary,
    LOCATION_KEYS,
    get_location_key,
)
from flightfinder.config import Config, get_config, set_config
from flightfinder.cache import ResponseCache, get_cache, clear_cache
from flightfinder.alerts import PriceAlert, AlertMatch, DealAlertManager
from flightfinder.discord import DiscordNotifier, DiscordConfig, send_to_discord
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
    "HotelFinder",
    # Flight Models
    "Flight",
    "Location",
    "Itinerary",
    "RoundTrip",
    "Segment",
    # Hotel Models
    "Hotel",
    "HotelRate",
    "HotelRates",
    "HotelSearchResults",
    "HotelLocation",
    "HotelPriceRange",
    "HotelReviewSummary",
    "LOCATION_KEYS",
    "get_location_key",
    # Alerts
    "PriceAlert",
    "AlertMatch",
    "DealAlertManager",
    # Discord
    "DiscordNotifier",
    "DiscordConfig",
    "send_to_discord",
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
__version__ = "0.3.0"
