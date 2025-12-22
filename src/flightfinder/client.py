"""FlightFinder API client for Kiwi/Skypicker GraphQL API."""

import httpx
from datetime import date, datetime
from typing import Optional
from flightfinder.models import Location, Flight, Segment


class FlightFinder:
    """Client for searching flights via Kiwi/Skypicker API."""

    API_URL = "https://api.skypicker.com/umbrella/v2/graphql"
    DEFAULT_HEADERS = {
        "Content-Type": "application/json",
        "User-Agent": "FlightFinder/0.1.0",
    }

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                headers=self.DEFAULT_HEADERS,
            )
        return self._client

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def find_location(
        self,
        term: str,
        location_types: Optional[list[str]] = None,
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
        query = """
        query UmbrellaPlacesQuery(
            $search: PlacesSearchInput
            $filter: PlacesFilterInput
            $options: PlacesOptionsInput
            $first: Int!
        ) {
            places(search: $search, filter: $filter, options: $options, first: $first) {
                __typename
                ... on AppError {
                    error: message
                }
                ... on PlaceConnection {
                    edges {
                        node {
                            __typename
                            id
                            legacyId
                            name
                            slug
                            gps { lat lng }
                            ... on Station {
                                type
                                code
                                city {
                                    name
                                    country { name code }
                                }
                            }
                            ... on City {
                                code
                                country { name code }
                            }
                        }
                    }
                }
            }
        }
        """

        variables: dict = {
            "search": {"term": term},
            "first": limit,
        }

        if location_types:
            variables["filter"] = {"types": location_types}

        response = self._execute_query(query, variables)
        places_data = response.get("data", {}).get("places", {})

        if places_data.get("__typename") == "AppError":
            raise Exception(f"API Error: {places_data.get('error')}")

        edges = places_data.get("edges", [])

        locations = []
        for edge in edges:
            node = edge.get("node", {})
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

            # Map __typename to simpler type
            type_map = {"Station": "AIRPORT", "City": "CITY", "Country": "COUNTRY"}
            loc_type = node.get("type") or type_map.get(node_type, node_type)

            locations.append(
                Location(
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
            )

        return locations

    def search_flights(
        self,
        origin: str,
        destination: str = "anywhere",
        departure_from: Optional[date] = None,
        departure_to: Optional[date] = None,
        return_from: Optional[date] = None,
        return_to: Optional[date] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        cabin_class: str = "ECONOMY",
        max_stops: int = 2,
        sort_by: str = "PRICE",
        limit: int = 100,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
    ) -> list[Flight]:
        """
        Search for flights from origin to destination.

        Args:
            origin: Origin location ID (e.g., "SFO", "san-francisco_ca_us")
            destination: Destination location ID or "anywhere"
            departure_from: Earliest departure date
            departure_to: Latest departure date
            return_from: Earliest return date (for round trips)
            return_to: Latest return date (for round trips)
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
        query = """
        query SearchOneWayItinerariesQuery(
            $search: SearchOnewayInput
            $filter: ItinerariesFilterInput
            $options: ItinerariesOptionsInput
        ) {
            onewayItineraries(search: $search, filter: $filter, options: $options) {
                __typename
                ... on AppError {
                    error: message
                }
                ... on Itineraries {
                    itineraries {
                        __typename
                        ... on ItineraryOneWay {
                            id
                            price { amount }
                            priceEur { amount }
                            sector {
                                duration
                                sectorSegments {
                                    segment {
                                        source {
                                            station { code name }
                                            localTime
                                        }
                                        destination {
                                            station { code name }
                                            localTime
                                        }
                                        duration
                                        carrier { code name }
                                    }
                                }
                            }
                            bookingOptions {
                                edges {
                                    node { bookingUrl }
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        # Build itinerary specification (matching R package structure)
        # Note: "anywhere" is passed as a literal ID string, not a special object
        itinerary: dict = {
            "source": {"ids": [origin]},
            "destination": {"ids": [destination]},
        }

        # Add departure date range if specified
        if departure_from:
            itinerary["outboundDepartureDate"] = {
                "start": f"{departure_from.isoformat()}T00:00:00",
                "end": f"{(departure_to or departure_from).isoformat()}T23:59:59",
            }

        # Build search input
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

        # Build filter input (matching R package structure)
        filter_input: dict = {
            "allowChangeInboundDestination": True,
            "allowChangeInboundSource": True,
            "allowDifferentStationConnection": True,
            "enableSelfTransfer": True,
            "enableThrowAwayTicketing": True,
            "enableTrueHiddenCity": True,
            "transportTypes": ["FLIGHT"],
            "contentProviders": ["KIWI", "FRESH", "KAYAK"],
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

        # Build options
        options = {
            "sortBy": sort_by,
            "mergePriceDiffRule": "INCREASED",
            "currency": "usd",
            "locale": "en",
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

        # Use featureName parameter for flight search
        response = self._execute_query(
            query, variables, feature_name="SearchOneWayItinerariesQuery"
        )

        result = response.get("data", {}).get("onewayItineraries", {})

        if result.get("__typename") == "AppError":
            raise Exception(f"API Error: {result.get('error')}")

        itineraries = result.get("itineraries", [])

        flights = []
        for itin in itineraries:
            try:
                flight = self._parse_itinerary(itin)
                if flight:
                    flights.append(flight)
            except Exception:
                continue  # Skip malformed entries

        return flights

    def search_anywhere(
        self,
        origin: str,
        departure_from: Optional[date] = None,
        departure_to: Optional[date] = None,
        **kwargs,
    ) -> list[Flight]:
        """
        Search for flights from origin to anywhere.
        Convenience wrapper around search_flights with destination="anywhere".
        """
        return self.search_flights(
            origin=origin,
            destination="anywhere",
            departure_from=departure_from,
            departure_to=departure_to,
            **kwargs,
        )

    def _execute_query(
        self, query: str, variables: dict, feature_name: Optional[str] = None
    ) -> dict:
        """Execute a GraphQL query and return the response."""
        payload = {
            "query": query,
            "variables": variables,
        }

        url = self.API_URL
        if feature_name:
            url = f"{url}?featureName={feature_name}"

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def _parse_itinerary(self, data: dict) -> Optional[Flight]:
        """Parse a raw itinerary response into a Flight object."""
        sector = data.get("sector", {})
        segments_data = sector.get("sectorSegments", [])

        if not segments_data:
            return None

        # Parse segments
        segments = []
        for seg_wrapper in segments_data:
            seg = seg_wrapper.get("segment", {})
            source = seg.get("source", {})
            dest = seg.get("destination", {})
            carrier = seg.get("carrier", {}) or {}

            source_station = source.get("station", {}) or {}
            dest_station = dest.get("station", {}) or {}

            # Parse times
            source_time = source.get("localTime", "")
            dest_time = dest.get("localTime", "")

            try:
                departure_dt = datetime.fromisoformat(source_time.replace("Z", "+00:00"))
                arrival_dt = datetime.fromisoformat(dest_time.replace("Z", "+00:00"))
            except ValueError:
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

        # Extract price (API returns amount as string)
        price_data = data.get("price", {}) or {}
        price_str = price_data.get("amount", "0")
        try:
            price = float(price_str)
        except (ValueError, TypeError):
            price = 0.0

        # Extract booking URL
        booking_url = None
        booking_options = data.get("bookingOptions", {}).get("edges", [])
        if booking_options:
            booking_url = booking_options[0].get("node", {}).get("bookingUrl")

        # Calculate totals from first and last segment
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
