"""HTTP server for FlightFinder MCP - enables MCP Apps UI rendering.

Uses FastMCP for proper Streamable HTTP transport support.
Deploy to Fly.io or run locally with cloudflared.

Usage:
    python -m flightfinder.mcp_http_server
    python -m flightfinder.mcp_http_server --debug  # Verbose logging

Add the URL as a custom connector in Claude Desktop.
"""

import json
import logging
import os
import sys
import time
import traceback
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from hmac import compare_digest
from typing import Any

logger = logging.getLogger(__name__)

# Debug mode flag (set via --debug or FLIGHTFINDER_DEBUG env var)
DEBUG_MODE = os.environ.get("FLIGHTFINDER_DEBUG", "").lower() in ("1", "true", "yes")


def setup_debug_logging():
    """Configure verbose logging for debugging Claude Desktop connections."""
    # Configure root logger for verbose output
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )

    # Also enable debug for key libraries
    for name in ["mcp", "starlette", "uvicorn", "httpx"]:
        logging.getLogger(name).setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("DEBUG MODE ENABLED - Verbose logging active")
    logger.info("=" * 60)


# Default port for the HTTP server
DEFAULT_PORT = 3001
DEFAULT_HOST = "127.0.0.1"
TOKEN_ENV_VARS = ("FLIGHTFINDER_MCP_API_TOKEN", "FLIGHTFINDER_MCP_API_KEY")

LOCAL_BIND_HOSTS = {"127.0.0.1", "localhost", "::1"}
DEFAULT_ALLOWED_HOSTS = [
    "localhost",
    "localhost:*",
    "127.0.0.1",
    "127.0.0.1:*",
    "::1",
    "[::1]",
    "[::1]:*",
]
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:*",
    "http://127.0.0.1",
    "http://127.0.0.1:*",
    "http://[::1]",
    "http://[::1]:*",
]

# Track sessions for debugging
_active_sessions: dict[str, dict] = {}


@dataclass(frozen=True)
class HTTPAccessSettings:
    """Security settings applied to every HTTP route."""

    host: str
    allowed_hosts: tuple[str, ...]
    allowed_origins: tuple[str, ...]
    api_token: str | None = None

    @property
    def requires_token(self) -> bool:
        return self.api_token is not None


def _split_csv_values(values: Sequence[str] | None) -> list[str]:
    if not values:
        return []

    result: list[str] = []
    for value in values:
        result.extend(item.strip() for item in value.split(",") if item.strip())
    return result


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


def _is_local_bind_host(host: str) -> bool:
    return host.strip("[]").lower() in LOCAL_BIND_HOSTS


def _contains_wildcard(values: Sequence[str]) -> bool:
    return any(value.strip() == "*" for value in values)


def _env_token() -> str | None:
    for env_var in TOKEN_ENV_VARS:
        token = os.environ.get(env_var)
        if token:
            return token
    return None


def build_http_access_settings(
    host: str,
    allowed_hosts: Sequence[str] | None = None,
    allowed_origins: Sequence[str] | None = None,
    api_token: str | None = None,
) -> HTTPAccessSettings:
    """Build conservative HTTP access settings for the MCP server.

    Local development binds to loopback with local host/origin allowlists. Remote
    binds are allowed only when the caller supplies a token and explicit
    non-wildcard allowlists.
    """

    extra_hosts = _split_csv_values(allowed_hosts)
    extra_origins = _split_csv_values(allowed_origins)
    resolved_hosts = _dedupe([*DEFAULT_ALLOWED_HOSTS, *extra_hosts])
    resolved_origins = _dedupe([*DEFAULT_ALLOWED_ORIGINS, *extra_origins])
    resolved_token = api_token or _env_token()

    if _contains_wildcard(resolved_hosts):
        raise ValueError("MCP HTTP allowed hosts must be explicit; '*' is not allowed.")
    if _contains_wildcard(resolved_origins):
        raise ValueError("MCP HTTP allowed origins must be explicit; '*' is not allowed.")

    if not _is_local_bind_host(host):
        if not resolved_token:
            env_names = " or ".join(TOKEN_ENV_VARS)
            raise ValueError(f"Remote MCP HTTP binds require {env_names}.")
        if not extra_hosts:
            raise ValueError("Remote MCP HTTP binds require at least one --allowed-host value.")
        if not extra_origins:
            raise ValueError("Remote MCP HTTP binds require at least one --allowed-origin value.")

    return HTTPAccessSettings(
        host=host,
        allowed_hosts=resolved_hosts,
        allowed_origins=resolved_origins,
        api_token=resolved_token,
    )


def _matches_allowlist(value: str | None, allowed: Sequence[str]) -> bool:
    if not value:
        return False

    if value in allowed:
        return True

    return any(
        pattern.endswith(":*") and value.startswith(f"{pattern[:-2]}:") for pattern in allowed
    )


def validate_host_header(host: str | None, settings: HTTPAccessSettings) -> bool:
    return _matches_allowlist(host, settings.allowed_hosts)


def validate_origin_header(origin: str | None, settings: HTTPAccessSettings) -> bool:
    # Non-browser clients commonly omit Origin.
    return origin is None or _matches_allowlist(origin, settings.allowed_origins)


def validate_api_token(headers: Mapping[str, str], settings: HTTPAccessSettings) -> bool:
    if settings.api_token is None:
        return True

    authorization = headers.get("authorization") or headers.get("Authorization")
    if authorization and authorization.lower().startswith("bearer "):
        return compare_digest(authorization[7:].strip(), settings.api_token)

    api_token = headers.get("x-flightfinder-api-token") or headers.get("X-FlightFinder-API-Token")
    return bool(api_token and compare_digest(api_token, settings.api_token))


def create_http_access_middleware(settings: HTTPAccessSettings):
    """Create Starlette middleware for host/origin allowlists and API tokens."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response

    class HTTPAccessControlMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            if not validate_host_header(request.headers.get("host"), settings):
                return Response("Invalid Host header", status_code=421)

            if not validate_origin_header(request.headers.get("origin"), settings):
                return Response("Invalid Origin header", status_code=403)

            if not validate_api_token(request.headers, settings):
                return Response("Missing or invalid API token", status_code=401)

            return await call_next(request)

    return HTTPAccessControlMiddleware


def log_request_details(method: str, path: str, headers: dict, body: bytes | None = None):
    """Log detailed request information."""
    if not DEBUG_MODE:
        return

    logger.info("-" * 50)
    logger.info(f">>> INCOMING REQUEST: {method} {path}")
    logger.info(">>> Headers:")
    for key, value in sorted(headers.items()):
        # Mask potentially sensitive headers
        if key.lower() in ("authorization", "cookie"):
            value = f"{value[:20]}..." if len(value) > 20 else "[redacted]"
        logger.info(f"    {key}: {value}")

    if body:
        try:
            body_str = body.decode("utf-8")
            # Pretty print JSON
            try:
                body_json = json.loads(body_str)
                logger.info(f">>> Body (JSON): {json.dumps(body_json, indent=2)}")
            except json.JSONDecodeError:
                logger.info(
                    f">>> Body (raw): {body_str[:500]}{'...' if len(body_str) > 500 else ''}"
                )
        except UnicodeDecodeError:
            logger.info(f">>> Body: <binary {len(body)} bytes>")


def log_response_details(status: int, headers: dict, body_preview: str = ""):
    """Log detailed response information."""
    if not DEBUG_MODE:
        return

    logger.info(f"<<< RESPONSE: {status}")
    logger.info("<<< Headers:")
    for key, value in sorted(headers.items()):
        logger.info(f"    {key}: {value}")
    if body_preview:
        logger.info(
            f"<<< Body preview: {body_preview[:200]}{'...' if len(body_preview) > 200 else ''}"
        )
    logger.info("-" * 50)


def log_session_event(event: str, session_id: str | None = None, details: dict | None = None):
    """Log MCP session state changes."""
    if not DEBUG_MODE:
        return

    logger.info(f"[SESSION] {event}")
    if session_id:
        logger.info(f"    Session ID: {session_id}")
    if details:
        for key, value in details.items():
            logger.info(f"    {key}: {value}")


def create_debug_middleware(app):
    """Create Starlette middleware for request/response logging."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import StreamingResponse

    class DebugLoggingMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            start_time = time.time()

            # Log request
            headers = dict(request.headers)
            body = await request.body() if request.method in ("POST", "PUT", "PATCH") else None

            log_request_details(request.method, str(request.url), headers, body)

            # Check for session ID in headers (MCP protocol)
            session_id = headers.get("mcp-session-id")
            if session_id:
                log_session_event("Request with session", session_id)

            try:
                response = await call_next(request)
                elapsed = (time.time() - start_time) * 1000

                # Log response
                response_headers = dict(response.headers)
                response_headers["X-Response-Time"] = f"{elapsed:.2f}ms"

                # For non-streaming responses, capture body preview
                body_preview = ""
                if not isinstance(response, StreamingResponse):
                    if hasattr(response, "body"):
                        try:
                            body_preview = response.body.decode("utf-8")
                        except (AttributeError, UnicodeDecodeError):
                            pass

                log_response_details(response.status_code, response_headers, body_preview)

                # Log new session ID if created
                new_session_id = response_headers.get("mcp-session-id")
                if new_session_id and new_session_id != session_id:
                    log_session_event("New session created", new_session_id)
                    _active_sessions[new_session_id] = {
                        "created_at": time.time(),
                        "request_count": 1,
                    }
                elif session_id and session_id in _active_sessions:
                    _active_sessions[session_id]["request_count"] += 1

                logger.info(
                    f"[TIMING] {request.method} {request.url.path} -> {response.status_code} ({elapsed:.2f}ms)"
                )

                return response

            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.error(
                    f"[ERROR] {request.method} {request.url.path} failed after {elapsed:.2f}ms"
                )
                logger.error(f"[ERROR] Exception: {type(e).__name__}: {e}")
                logger.error(f"[ERROR] Stack trace:\n{traceback.format_exc()}")
                raise

    return DebugLoggingMiddleware


def _is_valid_location_code(query: str) -> bool:
    """Check if query looks like an existing location code.

    Returns True for:
    - 3-letter uppercase airport codes (SFO, NRT, JFK)
    - City codes with underscores (tokyo_jp, new-york_ny_us)
    - Already lowercase slugs (paris, london)
    """
    q = query.strip()
    if not q:
        return False
    # 3-letter airport codes (e.g., SFO, NRT)
    if len(q) == 3 and q.isalpha() and q.isupper():
        return True
    # City codes (e.g., tokyo_jp, new-york_ny_us)
    if "_" in q:
        return True
    # Lowercase slugs that look like codes (not mixed case city names)
    if q.islower() and q.isalpha() and len(q) <= 10:
        return True
    return False


def _resolve_location(query: str, finder: Any) -> tuple[str, str | None]:
    """Resolve a location query to a valid code.

    Args:
        query: Location string (city name or code)
        finder: FlightFinder instance for API calls

    Returns:
        (resolved_code, resolution_note)
        - resolved_code: The code to use for search
        - resolution_note: Explanation if resolution happened, None if already valid
    """
    # Check if already looks like a valid code
    if _is_valid_location_code(query):
        return query, None

    # Resolve via API
    try:
        locations = finder.find_location(term=query, limit=5)
    except Exception as e:
        logger.warning(f"Location resolution failed for '{query}': {e}")
        return query, f"Could not resolve '{query}': {e}"

    if not locations:
        return query, f"Could not resolve '{query}' - no matches found"

    # Prefer city code (broader coverage), then first airport
    city = next((loc for loc in locations if loc.type == "CITY"), None)
    if city:
        return city.id, f"Resolved '{query}' → {city.id} ({city.name})"

    # Fall back to first result (usually an airport)
    first = locations[0]
    return first.id, f"Resolved '{query}' → {first.id} ({first.name})"


def create_app():
    """Create the FastMCP HTTP application."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("MCP support requires the 'mcp' package.")
        print("Install with: pip install flightfinder[mcp-http]")
        sys.exit(1)

    from flightfinder.client import FlightFinder
    from flightfinder.hotel_client import HotelFinder
    from flightfinder.hotel_models import get_location_key

    # Create FastMCP server
    mcp = FastMCP("FlightFinder")

    # Register UI resources for MCP Apps
    # DISABLED: UI resources causing Claude.ai to hang during discovery phase
    # See: https://github.com/anthropics/claude-code/issues/XXX
    # for tool_name, (html_file, resource_uri) in UI_RESOURCES.items():
    #     html_path = UI_DIR / html_file
    #     if html_path.exists():
    #         mcp.add_resource(
    #             FileResource(
    #                 uri=resource_uri,
    #                 path=html_path,
    #                 name=f"{tool_name}-ui",
    #                 title=f"FlightFinder {tool_name.replace('_', ' ').title()} UI",
    #                 mime_type=MCP_APP_MIME_TYPE,
    #             )
    #         )

    # =========================================================================
    # MCP PROMPTS - These teach Claude how to use the tools intelligently
    # =========================================================================

    @mcp.prompt()
    def search_flights_guide() -> str:
        """Guide for searching flights effectively."""
        return """# FlightFinder Search Guide

When a user asks about flights, follow this workflow:

## Step 1: Resolve Location Codes
ALWAYS use `find_location` first to get proper airport/city codes:
- "Tokyo" → Use find_location("Tokyo") to get NRT (Narita), HND (Haneda), or tokyo_jp (city)
- "San Francisco" → SFO
- "New York" → JFK, EWR, LGA, or nyc_us (city)

## Step 2: Search Strategy
- For **round-trips**: Use `search_roundtrip` with the resolved codes
- For **one-way**: Use `search_flights`
- For **trip planning** (flights + hotels): Use `search_trip`

## Step 3: Handle Empty Results
If a search returns 0 results:
1. Try using the CITY code instead of airport (e.g., "tokyo_jp" instead of "NRT")
2. Expand the date range (increase search_window or days_from_now range)
3. Increase max_stops to 2
4. Try nearby airports

## Example Workflow
User: "Find flights from SF to Tokyo next month"

1. find_location("San Francisco") → SFO
2. find_location("Tokyo") → tokyo_jp (city), NRT, HND
3. search_roundtrip(origin="SFO", destination="tokyo_jp", days_from_now=30)
4. If empty, try: search_roundtrip(origin="SFO", destination="NRT", max_stops=2)
"""

    @mcp.prompt()
    def trip_planning_guide() -> str:
        """Comprehensive trip planning workflow."""
        return """# Trip Planning with FlightFinder

For comprehensive trip planning, use this approach:

## Quick Trip Search
Use `search_trip` for combined flight + hotel results:
```
search_trip(origin="SFO", destination="Tokyo", days_from_now=30, nights=7)
```

## Detailed Planning
1. **Resolve destination**: find_location("destination city")
2. **Search flights**: search_roundtrip with city code for best coverage
3. **Search hotels**: search_hotels with the city name
4. **Compare options**: Present flight + hotel combinations with total costs

## Supported Hotel Cities
Hotels are available for major cities: Paris, Tokyo, London, New York, Rome, Barcelona, etc.
Use the city NAME (not code) for hotel searches.

## Budget Planning
- Use max_price filters to stay within budget
- search_trip provides estimated_total combining cheapest flight + hotel
"""

    # UI metadata disabled - was causing Claude.ai to hang
    # meta={"ui": {"resourceUri": "app://flightfinder/flights", "csp": {"resourceDomains": ["https://unpkg.com"]}}}
    @mcp.tool()
    def search_flights(
        origin: str,
        destination: str,
        days_from_now: int = 30,
        search_window: int = 7,
        max_stops: int = 1,
        max_price: float | None = None,
        limit: int = 10,
    ) -> dict:
        """Search for one-way flights between airports.

        Args:
            origin: Origin airport code or city name (e.g., SFO, "San Francisco")
            destination: Destination airport code or city name (e.g., NRT, "Tokyo")
            days_from_now: Days from today to start searching
            search_window: Number of days to search
            max_stops: Maximum number of stops (0=direct only)
            max_price: Maximum price filter
            limit: Maximum results to return
        """
        departure_from = date.today() + timedelta(days=days_from_now)
        departure_to = departure_from + timedelta(days=search_window)

        with FlightFinder() as finder:
            # Auto-resolve location names to codes
            origin_code, origin_note = _resolve_location(origin, finder)
            dest_code, dest_note = _resolve_location(destination, finder)

            flights = finder.search_flights(
                origin=origin_code.upper()
                if origin_code.isalpha() and len(origin_code) == 3
                else origin_code,
                destination=dest_code,
                departure_from=departure_from,
                departure_to=departure_to,
                max_stops=max_stops,
                max_price=max_price,
                limit=limit,
            )

            result = {
                "count": len(flights),
                "search": {
                    "origin": origin_code,
                    "destination": dest_code,
                    "dates": f"{departure_from} to {departure_to}",
                },
                "flights": [
                    {
                        "price": f.price,
                        "origin": f.origin,
                        "destination": f.destination,
                        "departure": f.departure_time.isoformat(),
                        "arrival": f.arrival_time.isoformat(),
                        "duration": f.duration_formatted,
                        "stops": f.stops,
                        "carriers": f.carriers,
                        "booking_url": f.deep_link,
                    }
                    for f in flights
                ],
            }

            # Add resolution notes if any location was resolved
            if origin_note or dest_note:
                result["resolution"] = {}
                if origin_note:
                    result["resolution"]["origin"] = origin_note
                if dest_note:
                    result["resolution"]["destination"] = dest_note

            return result

    # UI metadata disabled - was causing Claude.ai to hang
    # meta={"ui": {"resourceUri": "app://flightfinder/roundtrip", "csp": {"resourceDomains": ["https://unpkg.com"]}}}
    @mcp.tool()
    def search_roundtrip(
        origin: str,
        destination: str,
        days_from_now: int = 30,
        min_days: int = 7,
        max_days: int = 14,
        max_stops: int = 1,
        max_price: float | None = None,
        limit: int = 10,
    ) -> dict:
        """Search for round-trip flights.

        Args:
            origin: Origin airport code or city name (e.g., SFO, "San Francisco")
            destination: Destination airport code or city name (e.g., NRT, "Tokyo")
            days_from_now: Days from today to depart
            min_days: Minimum trip length
            max_days: Maximum trip length
            max_stops: Maximum stops per leg
            max_price: Maximum total price
            limit: Maximum results
        """
        departure_from = date.today() + timedelta(days=days_from_now)
        departure_to = departure_from + timedelta(days=7)

        with FlightFinder() as finder:
            # Auto-resolve location names to codes
            origin_code, origin_note = _resolve_location(origin, finder)
            dest_code, dest_note = _resolve_location(destination, finder)

            roundtrips = finder.search_roundtrip(
                origin=origin_code.upper()
                if origin_code.isalpha() and len(origin_code) == 3
                else origin_code,
                destination=dest_code,
                departure_from=departure_from,
                departure_to=departure_to,
                min_days=min_days,
                max_days=max_days,
                max_stops=max_stops,
                max_price=max_price,
                limit=limit,
            )

            result = {
                "count": len(roundtrips),
                "search": {
                    "origin": origin_code,
                    "destination": dest_code,
                    "depart_around": str(departure_from),
                    "trip_duration": f"{min_days}-{max_days} days",
                },
                "roundtrips": [
                    {
                        "price": rt.price,
                        "price_with_bag": rt.price_with_bag,
                        "origin": rt.origin,
                        "destination": rt.destination,
                        "destination_city": rt.destination_city,
                        "outbound_date": rt.outbound.departure_time.date().isoformat(),
                        "return_date": rt.inbound.departure_time.date().isoformat(),
                        "trip_days": rt.trip_days,
                        "outbound_stops": rt.outbound.stops,
                        "return_stops": rt.inbound.stops,
                        "carriers": rt.all_carriers,
                        "booking_url": rt.booking_url,
                    }
                    for rt in roundtrips
                ],
            }

            # Add resolution notes if any location was resolved
            if origin_note or dest_note:
                result["resolution"] = {}
                if origin_note:
                    result["resolution"]["origin"] = origin_note
                if dest_note:
                    result["resolution"]["destination"] = dest_note

            return result

    # UI metadata disabled - was causing Claude.ai to hang
    # meta={"ui": {"resourceUri": "app://flightfinder/locations", "csp": {"resourceDomains": ["https://unpkg.com"]}}}
    @mcp.tool()
    def find_location(
        query: str,
        location_type: str | None = None,
        limit: int = 5,
    ) -> dict:
        """Search for airport or city codes.

        Args:
            query: Search term (e.g., "Tokyo", "San Francisco")
            location_type: Filter by AIRPORT, CITY, or COUNTRY
            limit: Maximum results
        """
        location_types = [location_type] if location_type else None

        with FlightFinder() as finder:
            locations = finder.find_location(
                term=query,
                location_types=location_types,
                limit=limit,
            )

            return {
                "count": len(locations),
                "query": query,
                "locations": [
                    {
                        "code": loc.id,
                        "name": loc.name,
                        "type": loc.type,
                        "city": loc.city,
                        "country": loc.country,
                        "country_code": loc.country_code,
                    }
                    for loc in locations
                ],
            }

    # UI metadata disabled - was causing Claude.ai to hang
    # meta={"ui": {"resourceUri": "app://flightfinder/hotels", "csp": {"resourceDomains": ["https://unpkg.com"]}}}
    @mcp.tool()
    def search_hotels(
        location: str,
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
        limit: int = 10,
    ) -> dict:
        """Search for hotels in a city.

        Args:
            location: City name (e.g., "Paris", "Tokyo")
            min_price: Minimum price per night
            max_price: Maximum price per night
            min_rating: Minimum rating (0-5)
            limit: Maximum results
        """
        location_key = get_location_key(location)
        if not location_key and not location.startswith("g"):
            return {
                "error": f"Unknown location: {location}",
                "suggestion": "Use a supported city name like Paris, Tokyo, London",
            }

        search_location = location_key or location

        with HotelFinder() as finder:
            results = finder.search_hotels(
                location=search_location,
                limit=limit,
                min_price=min_price,
                max_price=max_price,
                min_rating=min_rating,
            )

            return {
                "count": len(results.hotels),
                "total_available": results.total_count,
                "location": location,
                "hotels": [
                    {
                        "name": h.name,
                        "type": h.accommodation_type,
                        "price_range": str(h.price_range) if h.price_range else None,
                        "min_price": h.min_price,
                        "max_price": h.max_price,
                        "rating": h.rating,
                        "review_count": h.review_count,
                        "url": h.url,
                        "highlights": h.mentions[:3] if h.mentions else [],
                    }
                    for h in results.hotels
                ],
            }

    # UI metadata disabled - was causing Claude.ai to hang
    # meta={"ui": {"resourceUri": "app://flightfinder/trip", "csp": {"resourceDomains": ["https://unpkg.com"]}}}
    @mcp.tool()
    def search_trip(
        origin: str,
        destination: str,
        days_from_now: int = 30,
        nights: int = 7,
        max_flight_price: float | None = None,
        max_hotel_price: float | None = None,
        limit: int = 5,
    ) -> dict:
        """Search for flights AND hotels together for trip planning.

        Args:
            origin: Origin airport code or city name (e.g., SFO, "San Francisco")
            destination: Destination city name (e.g., "Tokyo", "Paris")
            days_from_now: Days from today to depart
            nights: Number of nights
            max_flight_price: Max flight budget
            max_hotel_price: Max hotel per night budget
            limit: Results per category
        """
        departure_from = date.today() + timedelta(days=days_from_now)
        departure_to = departure_from + timedelta(days=7)

        # Search flights with auto-resolution
        origin_note = None
        dest_note = None
        origin_code = origin
        dest_code = destination

        try:
            with FlightFinder() as finder:
                # Auto-resolve location names to codes
                origin_code, origin_note = _resolve_location(origin, finder)
                dest_code, dest_note = _resolve_location(destination, finder)

                roundtrips = finder.search_roundtrip(
                    origin=origin_code.upper()
                    if origin_code.isalpha() and len(origin_code) == 3
                    else origin_code,
                    destination=dest_code,
                    departure_from=departure_from,
                    departure_to=departure_to,
                    min_days=nights,
                    max_days=nights + 3,
                    max_stops=1,
                    max_price=max_flight_price,
                    limit=limit,
                )
                flights = [
                    {
                        "price": rt.price,
                        "dates": f"{rt.outbound.departure_time.date()} - {rt.inbound.departure_time.date()}",
                        "trip_days": rt.trip_days,
                        "carriers": rt.all_carriers[:2],
                    }
                    for rt in roundtrips
                ]
        except Exception as e:
            flights = []
            flight_error = str(e)
        else:
            flight_error = None

        result = {
            "origin": origin_code,
            "destination": dest_code,
            "dates": {"depart_around": str(departure_from), "nights": nights},
            "flights": flights,
            "hotels": [],
            "estimated_total": None,
        }

        if flight_error:
            result["flight_error"] = flight_error

        # Add resolution notes if any location was resolved
        if origin_note or dest_note:
            result["resolution"] = {}
            if origin_note:
                result["resolution"]["origin"] = origin_note
            if dest_note:
                result["resolution"]["destination"] = dest_note

        # Search hotels
        location_key = get_location_key(destination)
        if location_key:
            try:
                with HotelFinder() as finder:
                    hotels = finder.search_hotels(
                        location=location_key,
                        limit=limit,
                        max_price=max_hotel_price,
                    )
                    result["hotels"] = [
                        {
                            "name": h.name,
                            "price_per_night": h.min_price,
                            "rating": h.rating,
                            "type": h.accommodation_type,
                        }
                        for h in hotels.hotels
                    ]
            except Exception as e:
                result["hotel_error"] = str(e)
        else:
            result["hotel_note"] = f"Hotel search not available for '{destination}'."

        # Calculate estimated total
        if result["flights"] and result["hotels"]:
            min_flight = min(f["price"] for f in result["flights"])
            hotel_prices = [h["price_per_night"] for h in result["hotels"] if h["price_per_night"]]
            if hotel_prices:
                min_hotel = min(hotel_prices)
                result["estimated_total"] = {
                    "flight": min_flight,
                    "hotel_per_night": min_hotel,
                    "hotel_total": min_hotel * nights,
                    "total": min_flight + (min_hotel * nights),
                    "nights": nights,
                }

        return result

    # Add health check route with debug info
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request):
        from starlette.responses import JSONResponse

        response_data = {
            "status": "healthy",
            "service": "flightfinder-mcp",
            "debug_mode": DEBUG_MODE,
        }

        # Include session info in debug mode
        if DEBUG_MODE:
            response_data["active_sessions"] = len(_active_sessions)
            response_data["sessions"] = {
                sid: {
                    "age_seconds": int(time.time() - info["created_at"]),
                    "request_count": info["request_count"],
                }
                for sid, info in _active_sessions.items()
            }

        return JSONResponse(response_data)

    # Add debug route for testing MCP protocol details
    @mcp.custom_route("/debug/info", methods=["GET"])
    async def debug_info(request):
        from starlette.responses import JSONResponse

        if not DEBUG_MODE:
            return JSONResponse({"error": "Debug mode not enabled"}, status_code=403)

        return JSONResponse(
            {
                "debug_mode": True,
                "active_sessions": dict(_active_sessions),
                "tools_registered": list(mcp._tools.keys())
                if hasattr(mcp, "_tools")
                else "unknown",
                "server_info": {
                    "name": "FlightFinder",
                    "transport": "streamable-http",
                },
            }
        )

    return mcp


def main():
    """Entry point for the HTTP server."""
    global DEBUG_MODE

    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="FlightFinder MCP HTTP Server")
    parser.add_argument(
        "--host",
        default=os.environ.get("FLIGHTFINDER_MCP_HOST", DEFAULT_HOST),
        help=f"Bind host (default: {DEFAULT_HOST}; set FLIGHTFINDER_MCP_HOST to override)",
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--allowed-host",
        action="append",
        default=[],
        help="Allowed Host header. Repeat or comma-separate values. Required for non-local binds.",
    )
    parser.add_argument(
        "--allowed-origin",
        action="append",
        default=[],
        help="Allowed browser Origin. Repeat or comma-separate values. Required for non-local binds.",
    )
    parser.add_argument(
        "--api-token",
        default=None,
        help="Bearer/API token for HTTP access. Prefer FLIGHTFINDER_MCP_API_TOKEN.",
    )
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging")
    args = parser.parse_args()

    # Enable debug mode if flag or env var set
    if args.debug or os.environ.get("FLIGHTFINDER_DEBUG", "").lower() in ("1", "true", "yes"):
        DEBUG_MODE = True
        setup_debug_logging()

    try:
        access_settings = build_http_access_settings(
            host=args.host,
            allowed_hosts=args.allowed_host,
            allowed_origins=args.allowed_origin,
            api_token=args.api_token,
        )
    except ValueError as exc:
        parser.error(str(exc))

    mcp = create_app()

    from mcp.server.transport_security import TransportSecuritySettings

    # Local-only by default. Remote binds must opt in with auth and explicit allowlists.
    mcp.settings.host = args.host
    mcp.settings.port = args.port
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=list(access_settings.allowed_hosts),
        allowed_origins=list(access_settings.allowed_origins),
    )

    starlette_app = mcp.streamable_http_app()
    starlette_app.add_middleware(create_http_access_middleware(access_settings))
    if DEBUG_MODE:
        starlette_app.add_middleware(create_debug_middleware(starlette_app))

    print(f"\n{'=' * 60}")
    print("FlightFinder MCP HTTP Server (FastMCP)")
    print(f"{'=' * 60}")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Debug mode: {'ENABLED' if DEBUG_MODE else 'disabled'}")
    print("   Transport: Streamable HTTP")
    print("   DNS rebinding protection: ENABLED")
    print(
        f"   API token required: {'yes' if access_settings.requires_token else 'no (loopback only)'}"
    )
    print(f"   Allowed hosts: {', '.join(access_settings.allowed_hosts)}")
    print(f"   Allowed origins: {', '.join(access_settings.allowed_origins)}")
    print("\nEndpoints:")
    print(f"   Health:  http://{args.host}:{args.port}/health")
    print(f"   MCP:     http://{args.host}:{args.port}/mcp")
    if DEBUG_MODE:
        print(f"   Debug:   http://{args.host}:{args.port}/debug/info")
    print("\nFor remote/tunnel use:")
    print("   FLIGHTFINDER_MCP_API_TOKEN=<token> \\")
    print("     flightfinder-mcp-http --host 0.0.0.0 \\")
    print("     --allowed-host <public-host> --allowed-origin <trusted-origin>")
    print(f"{'=' * 60}\n")

    if DEBUG_MODE:
        logger.info("Starting server with debug logging enabled...")

    # Run with Streamable HTTP transport
    async def run_server():
        import uvicorn

        config = uvicorn.Config(
            starlette_app,
            host=mcp.settings.host,
            port=mcp.settings.port,
            log_level=mcp.settings.log_level.lower(),
        )
        server = uvicorn.Server(config)
        await server.serve()

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
