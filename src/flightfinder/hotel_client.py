"""HotelFinder API client for Xotelo hotel search API."""

import logging
import time
from datetime import date

import httpx

from flightfinder.cache import ResponseCache, get_cache
from flightfinder.exceptions import (
    APIError,
    NetworkError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from flightfinder.hotel_models import (
    Hotel,
    HotelLocation,
    HotelPriceRange,
    HotelRate,
    HotelRates,
    HotelReviewSummary,
    HotelSearchResults,
    get_location_key,
)

logger = logging.getLogger(__name__)


class HotelFinder:
    """Client for searching hotels via Xotelo API (TripAdvisor data)."""

    BASE_URL = "https://data.xotelo.com/api"

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        cache_enabled: bool = True,
        cache_ttl: int = 300,
    ):
        """
        Initialize the HotelFinder client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            cache_enabled: Enable response caching
            cache_ttl: Cache time-to-live in seconds
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.Client | None = None
        self._cache: ResponseCache | None = (
            get_cache(max_size=100, default_ttl=cache_ttl)
            if cache_enabled
            else None
        )

        logger.debug(
            f"HotelFinder initialized with timeout={timeout}s, "
            f"cache={'enabled' if self._cache else 'disabled'}"
        )

    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "FlightFinder/0.2.0 (Hotel Search)",
                },
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
            logger.debug("HotelFinder client closed")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def search_hotels(
        self,
        location: str,
        limit: int = 30,
        offset: int = 0,
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
        accommodation_types: list[str] | None = None,
    ) -> HotelSearchResults:
        """
        Search for hotels in a location.

        Args:
            location: City name (e.g., "New York") or TripAdvisor location key (e.g., "g60763")
            limit: Maximum results to return (max 100)
            offset: Pagination offset
            min_price: Minimum nightly price filter
            max_price: Maximum nightly price filter
            min_rating: Minimum rating filter (0-5)
            accommodation_types: Filter by type (Hotel, Hostel, etc.)

        Returns:
            HotelSearchResults with matching hotels

        Raises:
            ValidationError: If location is empty or invalid
            APIError: If API returns an error
            NetworkError: If connection fails
        """
        if not location or not location.strip():
            raise ValidationError("Location cannot be empty", field="location")

        # Resolve location to key if it's a city name
        location_key = location if location.startswith("g") else get_location_key(location)

        if not location_key:
            raise ValidationError(
                f"Unknown location: '{location}'. "
                "Use a city name like 'New York' or a TripAdvisor location key like 'g60763'",
                field="location",
            )

        # Clamp limit
        limit = min(limit, 100)

        logger.info(f"Searching hotels in location: {location_key}")

        params = {
            "location_key": location_key,
            "limit": limit,
            "offset": offset,
        }

        response = self._execute_request("/list", params)

        if response.get("error"):
            error_msg = response["error"].get("message", "Unknown error")
            raise APIError(f"Hotel search failed: {error_msg}")

        result = response.get("result", {})
        hotels = self._parse_hotel_list(result.get("list", []))

        # Apply client-side filters
        if min_price is not None:
            hotels = [h for h in hotels if h.min_price and h.min_price >= min_price]
        if max_price is not None:
            hotels = [h for h in hotels if h.max_price and h.max_price <= max_price]
        if min_rating is not None:
            hotels = [h for h in hotels if h.rating and h.rating >= min_rating]
        if accommodation_types:
            types_lower = [t.lower() for t in accommodation_types]
            hotels = [h for h in hotels if h.accommodation_type.lower() in types_lower]

        return HotelSearchResults(
            location_key=location_key,
            total_count=result.get("total_count", len(hotels)),
            hotels=hotels,
            offset=result.get("offset", offset),
            limit=result.get("limit", limit),
        )

    def get_hotel_rates(
        self,
        hotel_key: str,
        check_in: date,
        check_out: date,
        rooms: int = 1,
        adults: int = 2,
        currency: str = "USD",
    ) -> HotelRates:
        """
        Get real-time rates for a specific hotel.

        Note: The free tier of Xotelo may not return real-time rates.
        Rates are sourced from various OTAs when available.

        Args:
            hotel_key: Hotel key from search results (e.g., "g60763-d23448880")
            check_in: Check-in date
            check_out: Check-out date
            rooms: Number of rooms (max 8)
            adults: Number of adults (max 32)
            currency: Currency code (USD, EUR, GBP, etc.)

        Returns:
            HotelRates with available rates

        Raises:
            ValidationError: If parameters are invalid
            APIError: If API returns an error
        """
        if not hotel_key or not hotel_key.strip():
            raise ValidationError("Hotel key cannot be empty", field="hotel_key")

        if check_out <= check_in:
            raise ValidationError(
                "Check-out date must be after check-in date",
                field="check_out",
            )

        if check_in < date.today():
            raise ValidationError(
                "Check-in date cannot be in the past",
                field="check_in",
            )

        rooms = min(rooms, 8)
        adults = min(adults, 32)

        logger.info(
            f"Getting rates for hotel: {hotel_key}, "
            f"dates: {check_in} to {check_out}"
        )

        params = {
            "hotel_key": hotel_key,
            "chk_in": check_in.isoformat(),
            "chk_out": check_out.isoformat(),
            "rooms": rooms,
            "adults": adults,
            "currency": currency,
        }

        response = self._execute_request("/rates", params)

        if response.get("error"):
            error_msg = response["error"].get("message", "Unknown error")
            # Don't raise for empty rates, just return empty result
            if "invalid hotel_key" in error_msg.lower():
                raise ValidationError(f"Invalid hotel key: {hotel_key}", field="hotel_key")
            if "too far in the past" in error_msg.lower():
                raise ValidationError(
                    f"Check-in date {check_in} is in the past",
                    field="check_in",
                )
            raise APIError(f"Rate lookup failed: {error_msg}")

        result = response.get("result", {})
        rates = self._parse_rates(result.get("rates", []))

        return HotelRates(
            hotel_key=hotel_key,
            check_in=check_in,
            check_out=check_out,
            currency=result.get("currency", currency),
            rates=rates,
        )

    def _parse_hotel_list(self, hotels_data: list) -> list[Hotel]:
        """Parse a list of hotel data from the API response."""
        hotels = []
        for data in hotels_data:
            try:
                hotel = self._parse_hotel(data)
                if hotel:
                    hotels.append(hotel)
            except Exception as e:
                logger.warning(f"Failed to parse hotel: {e}")
                continue
        return hotels

    def _parse_hotel(self, data: dict) -> Hotel | None:
        """Parse a single hotel from API response."""
        review_data = data.get("review_summary")
        review_summary = None
        if review_data:
            review_summary = HotelReviewSummary(
                rating=review_data.get("rating", 0),
                count=review_data.get("count", 0),
            )

        price_data = data.get("price_ranges")
        price_range = None
        if price_data:
            price_range = HotelPriceRange(
                minimum=price_data.get("minimum", 0),
                maximum=price_data.get("maximum", 0),
            )

        geo_data = data.get("geo")
        location = None
        if geo_data:
            location = HotelLocation(
                latitude=geo_data.get("latitude", 0),
                longitude=geo_data.get("longitude", 0),
            )

        return Hotel(
            key=data.get("key", ""),
            name=data.get("name", ""),
            accommodation_type=data.get("accommodation_type", "Hotel"),
            url=data.get("url"),
            review_summary=review_summary,
            price_range=price_range,
            location=location,
            image_url=data.get("image"),
            mentions=data.get("mentions", []),
            labels=data.get("merchandising_labels", []),
        )

    def _parse_rates(self, rates_data: list) -> list[HotelRate]:
        """Parse rate data from API response."""
        rates = []
        for data in rates_data:
            try:
                rate = HotelRate(
                    provider=data.get("provider", data.get("vendor", "Unknown")),
                    price=float(data.get("price", data.get("rate", 0))),
                    currency=data.get("currency", "USD"),
                    room_type=data.get("room_type"),
                    is_refundable=data.get("is_refundable"),
                    url=data.get("url", data.get("link")),
                )
                rates.append(rate)
            except Exception as e:
                logger.warning(f"Failed to parse rate: {e}")
                continue
        return rates

    def _execute_request(self, endpoint: str, params: dict) -> dict:
        """
        Execute an API request with retry logic and caching.

        Args:
            endpoint: API endpoint (e.g., "/list", "/rates")
            params: Query parameters

        Returns:
            API response as dictionary
        """
        cache_key = f"{endpoint}:{str(sorted(params.items()))}"

        # Check cache
        if self._cache:
            cached = self._cache.get(endpoint, params)
            if cached is not None:
                logger.debug("Returning cached response")
                return cached

        url = f"{self.BASE_URL}{endpoint}"

        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"API request attempt {attempt + 1}/{self.max_retries}: {endpoint}")

                response = self.client.get(url, params=params)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited. Retry after {retry_after}s")
                    raise RateLimitError(retry_after=retry_after)

                # Handle unauthorized (RapidAPI required for some endpoints)
                if response.status_code == 401:
                    result = response.json()
                    error_msg = result.get("error", {}).get("message", "Unauthorized")
                    raise APIError(
                        f"API access denied: {error_msg}",
                        status_code=401,
                    )

                response.raise_for_status()
                result = response.json()

                # Cache successful response
                if self._cache and not result.get("error"):
                    self._cache.set(endpoint, params, result)

                return result

            except httpx.TimeoutException as e:
                last_error = TimeoutError(f"Request timed out: {e}", original_error=e)
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")

            except httpx.ConnectError as e:
                last_error = NetworkError(f"Connection failed: {e}", original_error=e)
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")

            except RateLimitError:
                raise

            except httpx.HTTPStatusError as e:
                last_error = APIError(
                    f"HTTP error: {e}",
                    status_code=e.response.status_code,
                    response_body=e.response.text,
                )
                logger.error(f"HTTP error {e.response.status_code}: {e}")
                # Don't retry client errors
                if 400 <= e.response.status_code < 500:
                    raise last_error

            except Exception as e:
                last_error = NetworkError(f"Unexpected error: {e}", original_error=e)
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")

            # Exponential backoff
            if attempt < self.max_retries - 1:
                delay = 1.0 * (2.0 ** attempt)
                logger.debug(f"Retrying in {delay:.1f}s...")
                time.sleep(delay)

        if last_error:
            raise last_error
        raise NetworkError("Request failed after all retries")

    def cache_stats(self) -> dict | None:
        """Get cache statistics if caching is enabled."""
        if self._cache:
            return self._cache.stats()
        return None

    def clear_cache(self) -> int:
        """Clear the response cache. Returns number of entries cleared."""
        if self._cache:
            return self._cache.clear()
        return 0
