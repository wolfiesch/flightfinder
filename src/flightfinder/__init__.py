"""FlightFinder - Python client for Kiwi/Skypicker flight search API and Xotelo hotel search."""

from flightfinder.alerts import AlertMatch, DealAlertManager, PriceAlert
from flightfinder.async_client import AsyncFlightFinder
from flightfinder.cache import ResponseCache, clear_cache, get_cache
from flightfinder.client import FlightFinder
from flightfinder.config import Config, get_config, set_config
from flightfinder.discord import DiscordConfig, DiscordNotifier, send_to_discord
from flightfinder.exceptions import (
    APIError,
    ConfigurationError,
    FlightFinderError,
    NetworkError,
    ParseError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from flightfinder.hotel_client import HotelFinder
from flightfinder.hotel_models import (
    LOCATION_KEYS,
    Hotel,
    HotelLocation,
    HotelPriceRange,
    HotelRate,
    HotelRates,
    HotelReviewSummary,
    HotelSearchResults,
    get_location_key,
)
from flightfinder.models import Flight, Itinerary, Location, RoundTrip, Segment

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
__version__ = "1.0.0"

# Optional MCP server export (requires mcp package)
def _load_mcp_server():
    """Load MCP server if available."""
    try:
        from flightfinder.mcp_server import create_server
        return create_server
    except ImportError:
        return None


create_mcp_server = _load_mcp_server()
if create_mcp_server is not None:
    __all__.append("create_mcp_server")
