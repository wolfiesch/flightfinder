"""Async FlightFinder API client for Kiwi/Skypicker GraphQL API."""

import asyncio
import logging
from datetime import date, datetime, timedelta

import httpx

from flightfinder.cache import ResponseCache, get_cache
from flightfinder.config import Config, get_config
from flightfinder.exceptions import (
    APIError,
    NetworkError,
    ParseError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from flightfinder.models import Flight, Location, RoundTrip, Segment
from flightfinder.queries import ONEWAY_SEARCH_QUERY, PLACES_QUERY, ROUNDTRIP_SEARCH_QUERY

logger = logging.getLogger(__name__)


class AsyncFlightFinder:
    """Async client for searching flights via Kiwi/Skypicker API."""

    def __init__(
        self,
        config: Config | None = None,
        cache: ResponseCache | None = None,
        timeout: float | None = None,
    ):
        """
        Initialize the async FlightFinder client.

        Args:
            config: Optional configuration object. Uses global config if not provided.
            cache: Optional cache instance. Uses global cache if caching is enabled.
            timeout: Optional timeout override (deprecated, use config).
        """
        self.config = config or get_config()
        self._cache = cache if cache is not None else (
            get_cache(
                max_size=self.config.cache.max_size,
                default_ttl=self.config.cache.ttl_seconds,
            )
            if self.config.cache.enabled
            else None
        )
        self._client: httpx.AsyncClient | None = None

        # Support legacy timeout parameter
        if timeout is not None:
            self.config.api.timeout = timeout

        logger.debug(
            f"AsyncFlightFinder initialized with timeout={self.config.api.timeout}s, "
            f"cache={'enabled' if self._cache else 'disabled'}"
        )

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.api.timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": self.config.api.user_agent,
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the async HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.debug("AsyncFlightFinder client closed")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def find_location(
        self,
        term: str,
        location_types: list[str] | None = None,
        limit: int = 10,
    ) -> list[Location]:
        """
        Search for airports, cities, or countries by name.

        Args:
            term: Search query (e.g., "San Francisco", "SFO")
            location_types: Filter by type (AIRPORT, CITY, COUNTRY, REGION)
            limit: Maximum results to return

        Returns:
            List of matching locations
        """
        if not term or not term.strip():
            raise ValidationError("Search term cannot be empty", field="term")

        logger.info(f"Searching locations for: '{term}'")

        variables: dict = {
            "search": {"term": term},
            "first": limit,
        }

        if location_types:
            variables["filter"] = {"types": location_types}

        response = await self._execute_query(PLACES_QUERY, variables)
        places_data = response.get("data", {}).get("places", {})

        if places_data.get("__typename") == "AppError":
            error_msg = places_data.get("error", "Unknown error")
            logger.error(f"API error in location search: {error_msg}")
            raise APIError(f"Location search failed: {error_msg}")

        edges = places_data.get("edges", [])
        logger.debug(f"Found {len(edges)} location results")

        locations = []
        for edge in edges:
            try:
                location = self._parse_location(edge.get("node", {}))
                if location:
                    locations.append(location)
            except Exception as e:
                logger.warning(f"Failed to parse location: {e}")
                continue

        return locations

    def _parse_location(self, node: dict) -> Location | None:
        """Parse a location node from the API response."""
        gps = node.get("gps", {}) or {}
        node_type = node.get("__typename", "")

        city_name = None
        country_name = None
        country_code = None

        if "city" in node and node["city"]:
            city_name = node["city"].get("name")
            if "country" in node["city"] and node["city"]["country"]:
                country_name = node["city"]["country"].get("name")
                country_code = node["city"]["country"].get("code")
        elif "country" in node and node["country"]:
            country_name = node["country"].get("name")
            country_code = node["country"].get("code")

        type_map = {"Station": "AIRPORT", "City": "CITY", "Country": "COUNTRY"}
        loc_type = node.get("type") or type_map.get(node_type, node_type)

        return Location(
            id=node.get("legacyId") or node.get("id", ""),
            name=node.get("name", ""),
            slug=node.get("slug", ""),
            type=loc_type,
            city=city_name,
            country=country_name,
            country_code=country_code,
            latitude=gps.get("lat"),
            longitude=gps.get("lng"),
        )

    async def search_flights(
        self,
        origin: str,
        destination: str = "anywhere",
        departure_from: date | None = None,
        departure_to: date | None = None,
        adults: int | None = None,
        children: int | None = None,
        infants: int | None = None,
        cabin_class: str | None = None,
        max_stops: int | None = None,
        sort_by: str | None = None,
        limit: int | None = None,
        max_price: float | None = None,
        min_price: float | None = None,
    ) -> list[Flight]:
        """
        Search for flights from origin to destination.

        Args:
            origin: Origin location ID (e.g., "SFO")
            destination: Destination location ID or "anywhere"
            departure_from: Earliest departure date
            departure_to: Latest departure date
            adults: Number of adult passengers
            children: Number of child passengers
            infants: Number of infant passengers
            cabin_class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
            max_stops: Maximum number of stops (0 = direct only)
            sort_by: PRICE, QUALITY, DURATION, or POPULARITY
            limit: Maximum results
            max_price: Maximum price filter
            min_price: Minimum price filter

        Returns:
            List of Flight objects
        """
        if not origin or not origin.strip():
            raise ValidationError("Origin cannot be empty", field="origin")

        defaults = self.config.search_defaults
        adults = adults if adults is not None else defaults.adults
        children = children if children is not None else defaults.children
        infants = infants if infants is not None else defaults.infants
        cabin_class = cabin_class or defaults.cabin_class
        max_stops = max_stops if max_stops is not None else defaults.max_stops
        sort_by = sort_by or defaults.sort_by
        limit = limit if limit is not None else defaults.limit

        logger.info(
            f"Searching flights: {origin} → {destination}, "
            f"dates: {departure_from} to {departure_to}"
        )

        itinerary: dict = {
            "source": {"ids": [origin]},
            "destination": {"ids": [destination]},
        }

        if departure_from:
            itinerary["outboundDepartureDate"] = {
                "start": f"{departure_from.isoformat()}T00:00:00",
                "end": f"{(departure_to or departure_from).isoformat()}T23:59:59",
            }

        search = {
            "itinerary": itinerary,
            "passengers": {
                "adults": adults,
                "children": children,
                "infants": infants,
                "adultsHoldBags": 0,
                "adultsHandBags": 0,
                "childrenHoldBags": [],
                "childrenHandBags": [],
            },
            "cabinClass": {"cabinClass": cabin_class, "applyMixedClasses": False},
        }

        filter_input: dict = {
            "allowChangeInboundDestination": True,
            "allowChangeInboundSource": True,
            "allowDifferentStationConnection": True,
            "enableSelfTransfer": True,
            "enableThrowAwayTicketing": True,
            "enableTrueHiddenCity": True,
            "transportTypes": ["FLIGHT"],
            "contentProviders": defaults.content_providers,
            "flightsApiLimit": limit,
            "limit": limit,
            "maxStopsCount": max_stops,
        }

        if max_price is not None or min_price is not None:
            filter_input["price"] = {}
            if min_price is not None:
                filter_input["price"]["start"] = min_price
            if max_price is not None:
                filter_input["price"]["end"] = max_price

        options = {
            "sortBy": sort_by,
            "mergePriceDiffRule": "INCREASED",
            "currency": defaults.currency,
            "locale": defaults.locale,
            "partner": "skypicker",
            "affilID": "skypicker",
            "storeSearch": False,
            "searchStrategy": "REDUCED",
        }

        variables = {
            "search": search,
            "filter": filter_input,
            "options": options,
        }

        response = await self._execute_query(
            ONEWAY_SEARCH_QUERY, variables, feature_name="SearchOneWayItinerariesQuery"
        )

        result = response.get("data", {}).get("onewayItineraries", {})

        if result.get("__typename") == "AppError":
            error_msg = result.get("error", "Unknown error")
            logger.error(f"API error in flight search: {error_msg}")
            raise APIError(f"Flight search failed: {error_msg}")

        itineraries = result.get("itineraries", [])
        logger.debug(f"Found {len(itineraries)} flight results")

        flights = []
        for itin in itineraries:
            try:
                flight = self._parse_itinerary(itin)
                if flight:
                    flights.append(flight)
            except ParseError as e:
                logger.warning(f"Failed to parse itinerary: {e}")
                continue
            except Exception as e:
                logger.warning(f"Unexpected error parsing itinerary: {e}")
                continue

        logger.info(f"Successfully parsed {len(flights)} flights")
        return flights

    async def search_anywhere(
        self,
        origin: str,
        departure_from: date | None = None,
        departure_to: date | None = None,
        **kwargs,
    ) -> list[Flight]:
        """Search for flights from origin to anywhere."""
        return await self.search_flights(
            origin=origin,
            destination="anywhere",
            departure_from=departure_from,
            departure_to=departure_to,
            **kwargs,
        )

    async def search_roundtrip(
        self,
        origin: str,
        destination: str = "anywhere",
        departure_from: date | None = None,
        departure_to: date | None = None,
        return_from: date | None = None,
        return_to: date | None = None,
        min_days: int = 7,
        max_days: int = 21,
        adults: int | None = None,
        cabin_class: str | None = None,
        max_stops: int | None = None,
        sort_by: str | None = None,
        limit: int | None = None,
        max_price: float | None = None,
    ) -> list[RoundTrip]:
        """
        Search for round-trip flights.

        Args:
            origin: Origin airport code (e.g., "SFO")
            destination: Destination or "anywhere"
            departure_from: Earliest outbound departure date
            departure_to: Latest outbound departure date
            return_from: Earliest return date
            return_to: Latest return date
            min_days: Minimum trip duration in days
            max_days: Maximum trip duration in days
            adults: Number of passengers
            cabin_class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
            max_stops: Maximum stops per leg
            sort_by: PRICE, QUALITY, DURATION
            limit: Maximum results
            max_price: Maximum total price filter

        Returns:
            List of RoundTrip objects sorted by price
        """
        if not origin or not origin.strip():
            raise ValidationError("Origin cannot be empty", field="origin")

        if min_days < 1:
            raise ValidationError("min_days must be at least 1", field="min_days")

        if max_days < min_days:
            raise ValidationError(
                "max_days must be greater than or equal to min_days", field="max_days"
            )

        defaults = self.config.search_defaults
        adults = adults if adults is not None else defaults.adults
        cabin_class = cabin_class or defaults.cabin_class
        max_stops = max_stops if max_stops is not None else defaults.max_stops
        sort_by = sort_by or defaults.sort_by
        limit = limit if limit is not None else defaults.limit

        if departure_from is None:
            departure_from = date.today()
        if departure_to is None:
            departure_to = departure_from

        if return_from is None:
            return_from = departure_from + timedelta(days=min_days)
        if return_to is None:
            return_to = departure_to + timedelta(days=max_days)

        logger.info(
            f"Searching round-trip: {origin} → {destination}, "
            f"out: {departure_from}-{departure_to}, return: {return_from}-{return_to}"
        )

        itinerary: dict = {
            "source": {"ids": [origin]},
            "destination": {"ids": [destination]},
            "outboundDepartureDate": {
                "start": f"{departure_from.isoformat()}T00:00:00",
                "end": f"{departure_to.isoformat()}T23:59:59",
            },
            "inboundDepartureDate": {
                "start": f"{return_from.isoformat()}T00:00:00",
                "end": f"{return_to.isoformat()}T23:59:59",
            },
        }

        search = {
            "itinerary": itinerary,
            "passengers": {
                "adults": adults,
                "children": 0,
                "infants": 0,
                "adultsHoldBags": 0,
                "adultsHandBags": 0,
                "childrenHoldBags": [],
                "childrenHandBags": [],
            },
            "cabinClass": {"cabinClass": cabin_class, "applyMixedClasses": False},
        }

        filter_input: dict = {
            "allowChangeInboundDestination": True,
            "allowChangeInboundSource": True,
            "allowDifferentStationConnection": True,
            "enableSelfTransfer": True,
            "enableThrowAwayTicketing": True,
            "enableTrueHiddenCity": True,
            "transportTypes": ["FLIGHT"],
            "contentProviders": defaults.content_providers,
            "flightsApiLimit": limit,
            "limit": limit,
            "maxStopsCount": max_stops,
        }

        if max_price is not None:
            filter_input["price"] = {"end": max_price}

        options = {
            "sortBy": sort_by,
            "mergePriceDiffRule": "INCREASED",
            "currency": defaults.currency,
            "locale": defaults.locale,
            "partner": "skypicker",
            "affilID": "skypicker",
            "storeSearch": False,
            "searchStrategy": "REDUCED",
        }

        variables = {
            "search": search,
            "filter": filter_input,
            "options": options,
        }

        response = await self._execute_query(
            ROUNDTRIP_SEARCH_QUERY, variables, feature_name="SearchReturnItinerariesQuery"
        )

        result = response.get("data", {}).get("returnItineraries", {})

        if result.get("__typename") == "AppError":
            error_msg = result.get("error", "Unknown error")
            logger.error(f"API error in round-trip search: {error_msg}")
            raise APIError(f"Round-trip search failed: {error_msg}")

        itineraries = result.get("itineraries", [])
        logger.debug(f"Found {len(itineraries)} round-trip results")

        roundtrips = []
        for itin in itineraries:
            try:
                rt = self._parse_roundtrip(itin)
                if rt:
                    if min_days <= rt.trip_days <= max_days:
                        roundtrips.append(rt)
            except ParseError as e:
                logger.warning(f"Failed to parse round-trip: {e}")
                continue
            except Exception as e:
                logger.warning(f"Unexpected error parsing round-trip: {e}")
                continue

        logger.info(f"Successfully parsed {len(roundtrips)} round-trips")
        return roundtrips

    async def search_multiple_origins(
        self,
        origins: list[str],
        destination: str = "anywhere",
        departure_from: date | None = None,
        departure_to: date | None = None,
        **kwargs,
    ) -> dict[str, list[Flight]]:
        """
        Search flights from multiple origins concurrently.

        Args:
            origins: List of origin airport codes
            destination: Destination or "anywhere"
            departure_from: Earliest departure date
            departure_to: Latest departure date
            **kwargs: Additional search parameters

        Returns:
            Dictionary mapping origin codes to flight lists
        """
        async def search_origin(origin: str) -> tuple[str, list[Flight]]:
            flights = await self.search_flights(
                origin=origin,
                destination=destination,
                departure_from=departure_from,
                departure_to=departure_to,
                **kwargs,
            )
            return origin, flights

        tasks = [search_origin(origin) for origin in origins]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        flight_map: dict[str, list[Flight]] = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in concurrent search: {result}")
                continue
            origin, flights = result
            flight_map[origin] = flights

        return flight_map

    async def _execute_query(
        self, query: str, variables: dict, feature_name: str | None = None
    ) -> dict:
        """Execute a GraphQL query with retry logic and caching."""
        # Check cache first
        if self._cache:
            cached = self._cache.get(query, variables)
            if cached is not None:
                logger.debug("Returning cached response")
                return cached

        payload = {
            "query": query,
            "variables": variables,
        }

        url = self.config.api.base_url
        if feature_name:
            url = f"{url}?featureName={feature_name}"

        last_error: Exception | None = None
        for attempt in range(self.config.api.max_retries):
            try:
                logger.debug(f"API request attempt {attempt + 1}/{self.config.api.max_retries}")

                response = await self.client.post(url, json=payload)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited. Retry after {retry_after}s")
                    raise RateLimitError(retry_after=retry_after)

                response.raise_for_status()
                result = response.json()

                if self._cache:
                    self._cache.set(query, variables, result)

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
                if 400 <= e.response.status_code < 500:
                    raise last_error

            except Exception as e:
                last_error = NetworkError(f"Unexpected error: {e}", original_error=e)
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")

            if attempt < self.config.api.max_retries - 1:
                delay = self.config.api.retry_delay * (
                    self.config.api.retry_backoff ** attempt
                )
                logger.debug(f"Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)

        if last_error:
            raise last_error
        raise NetworkError("Request failed after all retries")

    def _parse_itinerary(self, data: dict) -> Flight | None:
        """Parse a raw itinerary response into a Flight object."""
        sector = data.get("sector", {})
        segments_data = sector.get("sectorSegments", [])

        if not segments_data:
            raise ParseError("No segments in itinerary", raw_data=data)

        segments = []
        for seg_wrapper in segments_data:
            seg = seg_wrapper.get("segment", {})
            source = seg.get("source", {})
            dest = seg.get("destination", {})
            carrier = seg.get("carrier", {}) or {}

            source_station = source.get("station", {}) or {}
            dest_station = dest.get("station", {}) or {}

            source_time = source.get("localTime", "")
            dest_time = dest.get("localTime", "")

            try:
                departure_dt = datetime.fromisoformat(source_time.replace("Z", "+00:00"))
                arrival_dt = datetime.fromisoformat(dest_time.replace("Z", "+00:00"))
            except ValueError as e:
                logger.debug(f"Failed to parse segment times: {e}")
                continue

            segments.append(
                Segment(
                    carrier=carrier.get("code", ""),
                    carrier_name=carrier.get("name"),
                    departure_time=departure_dt,
                    arrival_time=arrival_dt,
                    origin=source_station.get("code", ""),
                    origin_name=source_station.get("name"),
                    destination=dest_station.get("code", ""),
                    destination_name=dest_station.get("name"),
                    duration_minutes=(seg.get("duration") or 0) // 60,
                    cabin_class=seg.get("cabinClass"),
                )
            )

        if not segments:
            raise ParseError("No valid segments parsed", raw_data=data)

        price = self._parse_price(data.get("price", {}))

        booking_url = None
        booking_options = data.get("bookingOptions", {}).get("edges", [])
        if booking_options:
            booking_url = booking_options[0].get("node", {}).get("bookingUrl")

        first_seg = segments[0]
        last_seg = segments[-1]

        return Flight(
            id=data.get("id", ""),
            price=price,
            currency="USD",
            departure_time=first_seg.departure_time,
            arrival_time=last_seg.arrival_time,
            origin=first_seg.origin,
            origin_city=first_seg.origin_name,
            destination=last_seg.destination,
            destination_city=last_seg.destination_name,
            duration_minutes=(sector.get("duration") or 0) // 60,
            stops=len(segments) - 1,
            segments=segments,
            deep_link=booking_url,
        )

    def _parse_roundtrip(self, data: dict) -> RoundTrip | None:
        """Parse a round-trip itinerary response."""
        outbound_data = data.get("outbound", {})
        inbound_data = data.get("inbound", {})

        outbound = self._parse_sector(outbound_data)
        inbound = self._parse_sector(inbound_data)

        if not outbound or not inbound:
            raise ParseError("Missing outbound or inbound sector", raw_data=data)

        price = self._parse_price(data.get("price", {}))

        checked_bag_price = None
        bags_info = data.get("bagsInfo", {}) or {}
        included_bags = bags_info.get("includedCheckedBags", 0)
        if included_bags == 0:
            bag_tiers = bags_info.get("checkedBagTiers", [])
            if bag_tiers:
                tier_price = bag_tiers[0].get("tierPrice", {}).get("amount")
                if tier_price:
                    checked_bag_price = self._safe_float(tier_price)

        destination_country = None
        destination_city = None
        outbound_segments = outbound_data.get("sectorSegments", [])
        if outbound_segments:
            last_segment = outbound_segments[-1].get("segment", {})
            dest_station = last_segment.get("destination", {}).get("station", {})
            city_info = dest_station.get("city", {})
            if city_info:
                destination_city = city_info.get("name")
                country_info = city_info.get("country", {})
                if country_info:
                    destination_country = country_info.get("code")

        booking_url = None
        booking_options = data.get("bookingOptions", {}).get("edges", [])
        if booking_options:
            booking_url = booking_options[0].get("node", {}).get("bookingUrl")

        return RoundTrip(
            id=data.get("id", ""),
            price=price,
            currency="USD",
            outbound=outbound,
            inbound=inbound,
            booking_url=booking_url,
            checked_bag_price=checked_bag_price,
            destination_country=destination_country,
            destination_city=destination_city,
        )

    def _parse_sector(self, sector_data: dict) -> Flight | None:
        """Parse a sector (outbound or inbound) into a Flight object."""
        segments_data = sector_data.get("sectorSegments", [])

        if not segments_data:
            return None

        segments = []
        for seg_wrapper in segments_data:
            seg = seg_wrapper.get("segment", {})
            source = seg.get("source", {})
            dest = seg.get("destination", {})
            carrier = seg.get("carrier", {}) or {}

            source_station = source.get("station", {}) or {}
            dest_station = dest.get("station", {}) or {}

            source_time = source.get("localTime", "")
            dest_time = dest.get("localTime", "")

            try:
                departure_dt = datetime.fromisoformat(source_time.replace("Z", "+00:00"))
                arrival_dt = datetime.fromisoformat(dest_time.replace("Z", "+00:00"))
            except ValueError as e:
                logger.debug(f"Failed to parse segment times: {e}")
                continue

            segments.append(
                Segment(
                    carrier=carrier.get("code", ""),
                    carrier_name=carrier.get("name"),
                    departure_time=departure_dt,
                    arrival_time=arrival_dt,
                    origin=source_station.get("code", ""),
                    origin_name=source_station.get("name"),
                    destination=dest_station.get("code", ""),
                    destination_name=dest_station.get("name"),
                    duration_minutes=(seg.get("duration") or 0) // 60,
                    cabin_class=seg.get("cabinClass"),
                )
            )

        if not segments:
            return None

        first_seg = segments[0]
        last_seg = segments[-1]

        return Flight(
            id="",
            price=0,
            currency="USD",
            departure_time=first_seg.departure_time,
            arrival_time=last_seg.arrival_time,
            origin=first_seg.origin,
            origin_city=first_seg.origin_name,
            destination=last_seg.destination,
            destination_city=last_seg.destination_name,
            duration_minutes=(sector_data.get("duration") or 0) // 60,
            stops=len(segments) - 1,
            segments=segments,
        )

    def _parse_price(self, price_data: dict) -> float:
        """Safely parse a price from API response."""
        if not price_data:
            return 0.0
        return self._safe_float(price_data.get("amount", "0"))

    def _safe_float(self, value) -> float:
        """Safely convert a value to float."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

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
