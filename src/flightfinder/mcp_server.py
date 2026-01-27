"""MCP server for FlightFinder - AI agent integration via Model Context Protocol.

Supports MCP Apps for interactive UI rendering in Claude Desktop, VS Code, and ChatGPT.
"""

import json
import logging
from datetime import date, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# Tool to UI view mapping
TOOL_UI_VIEWS = {
    "search_flights": "flights",
    "search_roundtrip": "roundtrip",
    "search_hotels": "hotels",
    "search_trip": "trip",
    "find_location": "locations",
}


def create_server():
    """Create and configure the MCP server with FlightFinder tools.

    Returns:
        A configured MCP Server instance.

    Raises:
        ImportError: If the mcp package is not installed.
    """
    try:
        from mcp.server import Server
        from mcp.types import Resource, TextContent, Tool
    except ImportError as err:
        raise ImportError(
            "MCP support requires the 'mcp' package. "
            "Install with: pip install flightfinder[mcp]"
        ) from err

    from flightfinder.client import FlightFinder
    from flightfinder.hotel_client import HotelFinder
    from flightfinder.hotel_models import get_location_key

    # Import UI resources (optional - graceful degradation if not built)
    try:
        from flightfinder.ui_resources import (
            RESOURCE_MIME_TYPE,
            get_resource_uri,
            is_ui_available,
            list_available_views,
            load_ui_bundle,
        )
        UI_ENABLED = is_ui_available()
    except ImportError:
        UI_ENABLED = False
        logger.info("UI resources not available - text-only mode")

    server = Server("flightfinder")

    # Cache for the last result of each tool (for read_resource)
    _last_results: dict[str, dict] = {}

    def _get_tool_meta(tool_name: str) -> dict | None:
        """Get UI metadata for a tool if UI is available."""
        if not UI_ENABLED or tool_name not in TOOL_UI_VIEWS:
            return None
        view = TOOL_UI_VIEWS[tool_name]
        if view not in list_available_views():
            return None
        return {
            "ui": {
                "resourceUri": get_resource_uri(view),
            }
        }

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available FlightFinder tools with UI metadata."""
        tools = [
            Tool(
                name="search_flights",
                description="Search for one-way flights between airports",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Origin airport code (e.g., 'SFO', 'LAX', 'JFK')",
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination airport code or 'anywhere' for cheapest destinations",
                        },
                        "days_from_now": {
                            "type": "integer",
                            "description": "Days from today to start search (default: 30)",
                            "default": 30,
                        },
                        "search_window": {
                            "type": "integer",
                            "description": "Number of days to search within (default: 7)",
                            "default": 7,
                        },
                        "max_stops": {
                            "type": "integer",
                            "description": "Maximum number of stops (default: 1)",
                            "default": 1,
                        },
                        "max_price": {
                            "type": "number",
                            "description": "Maximum price in USD (optional)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 10)",
                            "default": 10,
                        },
                    },
                    "required": ["origin", "destination"],
                },
            ),
            Tool(
                name="search_roundtrip",
                description="Search for round-trip flights with specified trip duration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Origin airport code (e.g., 'SFO')",
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination airport code or 'anywhere'",
                        },
                        "days_from_now": {
                            "type": "integer",
                            "description": "Days from today to depart (default: 30)",
                            "default": 30,
                        },
                        "min_days": {
                            "type": "integer",
                            "description": "Minimum trip duration in days (default: 7)",
                            "default": 7,
                        },
                        "max_days": {
                            "type": "integer",
                            "description": "Maximum trip duration in days (default: 14)",
                            "default": 14,
                        },
                        "max_stops": {
                            "type": "integer",
                            "description": "Maximum stops per leg (default: 1)",
                            "default": 1,
                        },
                        "max_price": {
                            "type": "number",
                            "description": "Maximum total price in USD (optional)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results (default: 10)",
                            "default": 10,
                        },
                    },
                    "required": ["origin", "destination"],
                },
            ),
            Tool(
                name="find_location",
                description="Search for airport or city codes by name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search term (e.g., 'San Francisco', 'Tokyo', 'London')",
                        },
                        "location_type": {
                            "type": "string",
                            "enum": ["AIRPORT", "CITY", "COUNTRY"],
                            "description": "Filter by location type (optional)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results (default: 5)",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="search_hotels",
                description="Search for hotels in a city",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name (e.g., 'new york', 'tokyo', 'paris')",
                        },
                        "min_price": {
                            "type": "number",
                            "description": "Minimum nightly price in USD (optional)",
                        },
                        "max_price": {
                            "type": "number",
                            "description": "Maximum nightly price in USD (optional)",
                        },
                        "min_rating": {
                            "type": "number",
                            "description": "Minimum rating 0-5 (optional)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results (default: 10)",
                            "default": 10,
                        },
                    },
                    "required": ["location"],
                },
            ),
            Tool(
                name="search_trip",
                description="Search for flights AND hotels together for trip planning",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Origin airport code (e.g., 'SFO')",
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination city name (e.g., 'tokyo', 'new york')",
                        },
                        "days_from_now": {
                            "type": "integer",
                            "description": "Days from today to depart (default: 30)",
                            "default": 30,
                        },
                        "nights": {
                            "type": "integer",
                            "description": "Number of nights to stay (default: 7)",
                            "default": 7,
                        },
                        "max_flight_price": {
                            "type": "number",
                            "description": "Maximum flight price (optional)",
                        },
                        "max_hotel_price": {
                            "type": "number",
                            "description": "Maximum hotel price per night (optional)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Results per category (default: 5)",
                            "default": 5,
                        },
                    },
                    "required": ["origin", "destination"],
                },
            ),
        ]

        # Add UI metadata to tools if available
        if UI_ENABLED:
            for tool in tools:
                meta = _get_tool_meta(tool.name)
                if meta:
                    # Create a new Tool with annotations containing UI metadata
                    # Note: Tool.model_dump() gives us a dict we can modify
                    pass  # UI metadata is handled via resources

        return tools

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """List available UI resources."""
        if not UI_ENABLED:
            return []

        resources = []
        for tool_name, view in TOOL_UI_VIEWS.items():
            if view in list_available_views():
                resources.append(
                    Resource(
                        uri=get_resource_uri(view),
                        name=f"FlightFinder {view.title()} UI",
                        description=f"Interactive UI for {tool_name} results",
                        mimeType=RESOURCE_MIME_TYPE,
                    )
                )
        return resources

    @server.read_resource()
    async def read_resource(uri: str) -> str:
        """Read a UI resource and return the HTML with injected data."""
        if not UI_ENABLED:
            return json.dumps({"error": "UI not available"})

        # Extract view from URI (ui://flightfinder/flights -> flights)
        if not uri.startswith("ui://flightfinder/"):
            return json.dumps({"error": f"Unknown resource URI: {uri}"})

        view = uri.replace("ui://flightfinder/", "")

        # Find the tool that uses this view
        tool_name = None
        for name, v in TOOL_UI_VIEWS.items():
            if v == view:
                tool_name = name
                break

        if not tool_name:
            return json.dumps({"error": f"Unknown view: {view}"})

        # Get cached data for this tool
        data = _last_results.get(tool_name, {})

        try:
            html = load_ui_bundle(view, data)
            return html
        except Exception as e:
            logger.exception(f"Error loading UI bundle for {view}")
            return json.dumps({"error": str(e)})

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Execute a FlightFinder tool."""
        try:
            if name == "search_flights":
                result = _search_flights(arguments)
            elif name == "search_roundtrip":
                result = _search_roundtrip(arguments)
            elif name == "find_location":
                result = _find_location(arguments)
            elif name == "search_hotels":
                result = _search_hotels(arguments)
            elif name == "search_trip":
                result = _search_trip(arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}

            # Cache result for read_resource
            if not result.get("error"):
                _last_results[name] = result

            # Build response with text content
            contents = [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

            # Add UI metadata hint if available
            if UI_ENABLED and name in TOOL_UI_VIEWS:
                view = TOOL_UI_VIEWS[name]
                if view in list_available_views():
                    # Add a hint for the host that a UI is available
                    result["_ui"] = {
                        "resourceUri": get_resource_uri(view),
                        "mimeType": RESOURCE_MIME_TYPE,
                    }
                    # Update the text content with the UI hint
                    contents = [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

            return contents

        except Exception as e:
            logger.exception(f"Error executing tool {name}")
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    def _search_flights(args: dict) -> dict:
        """Execute one-way flight search."""
        days_from_now = args.get("days_from_now", 30)
        search_window = args.get("search_window", 7)
        departure_from = date.today() + timedelta(days=days_from_now)
        departure_to = departure_from + timedelta(days=search_window)

        with FlightFinder() as finder:
            flights = finder.search_flights(
                origin=args["origin"].upper(),
                destination=args["destination"],
                departure_from=departure_from,
                departure_to=departure_to,
                max_stops=args.get("max_stops", 1),
                max_price=args.get("max_price"),
                limit=args.get("limit", 10),
            )

            return {
                "count": len(flights),
                "search": {
                    "origin": args["origin"].upper(),
                    "destination": args["destination"],
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

    def _search_roundtrip(args: dict) -> dict:
        """Execute round-trip flight search."""
        days_from_now = args.get("days_from_now", 30)
        departure_from = date.today() + timedelta(days=days_from_now)
        departure_to = departure_from + timedelta(days=7)

        with FlightFinder() as finder:
            roundtrips = finder.search_roundtrip(
                origin=args["origin"].upper(),
                destination=args["destination"],
                departure_from=departure_from,
                departure_to=departure_to,
                min_days=args.get("min_days", 7),
                max_days=args.get("max_days", 14),
                max_stops=args.get("max_stops", 1),
                max_price=args.get("max_price"),
                limit=args.get("limit", 10),
            )

            return {
                "count": len(roundtrips),
                "search": {
                    "origin": args["origin"].upper(),
                    "destination": args["destination"],
                    "depart_around": str(departure_from),
                    "trip_duration": f"{args.get('min_days', 7)}-{args.get('max_days', 14)} days",
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

    def _find_location(args: dict) -> dict:
        """Execute location search."""
        location_types = [args["location_type"]] if args.get("location_type") else None

        with FlightFinder() as finder:
            locations = finder.find_location(
                term=args["query"],
                location_types=location_types,
                limit=args.get("limit", 5),
            )

            return {
                "count": len(locations),
                "query": args["query"],
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

    def _search_hotels(args: dict) -> dict:
        """Execute hotel search."""
        location = args["location"]

        # Check if it's a known location or a location key
        location_key = get_location_key(location)
        if not location_key and not location.startswith("g"):
            return {
                "error": f"Unknown location: {location}",
                "suggestion": "Use 'flights hotel-locations' CLI command to see supported cities",
            }

        search_location = location_key or location

        with HotelFinder() as finder:
            results = finder.search_hotels(
                location=search_location,
                limit=args.get("limit", 10),
                min_price=args.get("min_price"),
                max_price=args.get("max_price"),
                min_rating=args.get("min_rating"),
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

    def _search_trip(args: dict) -> dict:
        """Execute combined flight + hotel search."""
        days_from_now = args.get("days_from_now", 30)
        nights = args.get("nights", 7)
        departure_from = date.today() + timedelta(days=days_from_now)
        departure_to = departure_from + timedelta(days=7)

        destination = args["destination"]
        limit = args.get("limit", 5)

        result = {
            "origin": args["origin"].upper(),
            "destination": destination,
            "dates": {
                "depart_around": str(departure_from),
                "nights": nights,
            },
            "flights": [],
            "hotels": [],
            "estimated_total": None,
        }

        # Search flights
        try:
            with FlightFinder() as finder:
                roundtrips = finder.search_roundtrip(
                    origin=args["origin"].upper(),
                    destination=destination,
                    departure_from=departure_from,
                    departure_to=departure_to,
                    min_days=nights,
                    max_days=nights + 3,
                    max_stops=1,
                    max_price=args.get("max_flight_price"),
                    limit=limit,
                )
                result["flights"] = [
                    {
                        "price": rt.price,
                        "dates": f"{rt.outbound.departure_time.date()} - {rt.inbound.departure_time.date()}",
                        "trip_days": rt.trip_days,
                        "carriers": rt.all_carriers[:2],
                    }
                    for rt in roundtrips
                ]
        except Exception as e:
            result["flight_error"] = str(e)

        # Search hotels
        location_key = get_location_key(destination)
        if location_key:
            try:
                with HotelFinder() as finder:
                    hotels = finder.search_hotels(
                        location=location_key,
                        limit=limit,
                        max_price=args.get("max_hotel_price"),
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
            result["hotel_note"] = f"Hotel search not available for '{destination}'. Use a supported city name."

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

    return server


async def main():
    """Run the MCP server with stdio transport."""
    try:
        from mcp.server.stdio import stdio_server
    except ImportError:
        print("Error: MCP support requires the 'mcp' package.")
        print("Install with: pip install flightfinder[mcp]")
        return

    server = create_server()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
