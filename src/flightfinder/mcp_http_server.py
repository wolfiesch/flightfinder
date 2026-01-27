"""HTTP server for FlightFinder MCP - enables MCP Apps UI rendering.

MCP Apps requires HTTP transport (not stdio) to render interactive UIs.
Run this server and tunnel it via cloudflared for Claude Desktop support.

Usage:
    python -m flightfinder.mcp_http_server

Then in another terminal:
    npx cloudflared tunnel --url http://localhost:3001

Add the cloudflared URL as a custom connector in Claude Desktop.
"""

import asyncio
import json
import logging
import sys
from typing import Any

logger = logging.getLogger(__name__)

# Default port for the HTTP server
DEFAULT_PORT = 3001


async def create_http_server(port: int = DEFAULT_PORT):
    """Create and run the HTTP MCP server with MCP Apps support."""
    try:
        from starlette.applications import Starlette
        from starlette.middleware.cors import CORSMiddleware
        from starlette.requests import Request
        from starlette.responses import JSONResponse, Response
        from starlette.routing import Route
        import uvicorn
    except ImportError:
        print("HTTP server requires additional dependencies.")
        print("Install with: pip install starlette uvicorn")
        sys.exit(1)

    try:
        from mcp.server import Server
        from mcp.types import Resource, TextContent, Tool
    except ImportError:
        print("MCP support requires the 'mcp' package.")
        print("Install with: pip install flightfinder[mcp]")
        sys.exit(1)

    from flightfinder.mcp_server import create_server, TOOL_UI_VIEWS
    from flightfinder.ui_resources import (
        RESOURCE_MIME_TYPE,
        get_resource_uri,
        is_ui_available,
        list_available_views,
        load_ui_bundle,
    )

    # Create the MCP server
    mcp_server = create_server()

    # Cache for tool results (to populate UI resources)
    _last_results: dict[str, dict] = {}

    async def handle_mcp(request: Request) -> Response:
        """Handle MCP JSON-RPC requests."""
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)

        method = body.get("method", "")
        params = body.get("params", {})
        request_id = body.get("id")

        logger.info(f"MCP request: {method}")

        try:
            if method == "initialize":
                # Return server capabilities
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {"subscribe": False, "listChanged": False},
                    },
                    "serverInfo": {
                        "name": "flightfinder",
                        "version": "1.0.0",
                    },
                }

            elif method == "tools/list":
                # List available tools with UI metadata
                tools = []
                for name in TOOL_UI_VIEWS:
                    view = TOOL_UI_VIEWS[name]
                    tool_def = _get_tool_definition(name)
                    if tool_def:
                        # Add UI metadata
                        if is_ui_available() and view in list_available_views():
                            tool_def["_meta"] = {
                                "ui": {
                                    "resourceUri": get_resource_uri(view),
                                }
                            }
                        tools.append(tool_def)
                result = {"tools": tools}

            elif method == "tools/call":
                # Execute a tool
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})

                # Execute tool using local _execute_tool function
                tool_result = await _execute_tool(tool_name, arguments)

                # Cache for resource rendering
                if tool_name in TOOL_UI_VIEWS:
                    _last_results[tool_name] = tool_result

                result = {
                    "content": [
                        {"type": "text", "text": json.dumps(tool_result, default=str)}
                    ],
                    # Include structured content for MCP Apps
                    "structuredContent": tool_result,
                }

            elif method == "resources/list":
                # List UI resources
                resources = []
                if is_ui_available():
                    for tool_name, view in TOOL_UI_VIEWS.items():
                        if view in list_available_views():
                            resources.append({
                                "uri": get_resource_uri(view),
                                "name": f"FlightFinder {view.title()} UI",
                                "description": f"Interactive UI for {tool_name}",
                                "mimeType": RESOURCE_MIME_TYPE,
                            })
                result = {"resources": resources}

            elif method == "resources/read":
                # Return UI HTML with data
                uri = params.get("uri", "")
                if not uri.startswith("ui://flightfinder/"):
                    return JSONResponse(
                        {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": f"Unknown URI: {uri}"}},
                        status_code=200,
                    )

                view = uri.replace("ui://flightfinder/", "")
                tool_name = next((k for k, v in TOOL_UI_VIEWS.items() if v == view), None)

                if not tool_name or view not in list_available_views():
                    return JSONResponse(
                        {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": f"Unknown view: {view}"}},
                        status_code=200,
                    )

                # Get cached data or empty
                data = _last_results.get(tool_name, {})
                html = load_ui_bundle(view, data)

                result = {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": RESOURCE_MIME_TYPE,
                            "text": html,
                        }
                    ]
                }

            else:
                return JSONResponse(
                    {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}},
                    status_code=200,
                )

            return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": result})

        except Exception as e:
            logger.exception(f"Error handling {method}")
            return JSONResponse(
                {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": str(e)}},
                status_code=200,
            )

    async def _execute_tool(name: str, args: dict) -> dict:
        """Execute a FlightFinder tool and return the result."""
        from datetime import date, timedelta
        from flightfinder.client import FlightFinder
        from flightfinder.hotel_client import HotelFinder
        from flightfinder.hotel_models import get_location_key

        if name == "search_flights":
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

        elif name == "search_roundtrip":
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

        elif name == "find_location":
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

        elif name == "search_hotels":
            location = args["location"]
            location_key = get_location_key(location)
            if not location_key and not location.startswith("g"):
                return {
                    "error": f"Unknown location: {location}",
                    "suggestion": "Use a supported city name",
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

        elif name == "search_trip":
            days_from_now = args.get("days_from_now", 30)
            nights = args.get("nights", 7)
            departure_from = date.today() + timedelta(days=days_from_now)
            departure_to = departure_from + timedelta(days=7)
            destination = args["destination"]
            limit = args.get("limit", 5)

            result = {
                "origin": args["origin"].upper(),
                "destination": destination,
                "dates": {"depart_around": str(departure_from), "nights": nights},
                "flights": [],
                "hotels": [],
                "estimated_total": None,
            }

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
                result["hotel_note"] = f"Hotel search not available for '{destination}'."

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

        return {"error": f"Unknown tool: {name}"}

    def _get_tool_definition(name: str) -> dict | None:
        """Get the tool definition for a given tool name."""
        definitions = {
            "search_flights": {
                "name": "search_flights",
                "description": "Search for one-way flights between airports",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string", "description": "Origin airport code"},
                        "destination": {"type": "string", "description": "Destination airport code"},
                        "days_from_now": {"type": "integer", "default": 30},
                        "search_window": {"type": "integer", "default": 7},
                        "max_stops": {"type": "integer", "default": 1},
                        "max_price": {"type": "number"},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["origin", "destination"],
                },
            },
            "search_roundtrip": {
                "name": "search_roundtrip",
                "description": "Search for round-trip flights",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string"},
                        "destination": {"type": "string"},
                        "days_from_now": {"type": "integer", "default": 30},
                        "min_days": {"type": "integer", "default": 7},
                        "max_days": {"type": "integer", "default": 14},
                        "max_stops": {"type": "integer", "default": 1},
                        "max_price": {"type": "number"},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["origin", "destination"],
                },
            },
            "find_location": {
                "name": "find_location",
                "description": "Search for airport or city codes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "location_type": {"type": "string", "enum": ["AIRPORT", "CITY", "COUNTRY"]},
                        "limit": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
            },
            "search_hotels": {
                "name": "search_hotels",
                "description": "Search for hotels in a city",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                        "min_price": {"type": "number"},
                        "max_price": {"type": "number"},
                        "min_rating": {"type": "number"},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["location"],
                },
            },
            "search_trip": {
                "name": "search_trip",
                "description": "Search for flights AND hotels together",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string"},
                        "destination": {"type": "string"},
                        "days_from_now": {"type": "integer", "default": 30},
                        "nights": {"type": "integer", "default": 7},
                        "max_flight_price": {"type": "number"},
                        "max_hotel_price": {"type": "number"},
                        "limit": {"type": "integer", "default": 5},
                    },
                    "required": ["origin", "destination"],
                },
            },
        }
        return definitions.get(name)

    async def health_check(request: Request) -> Response:
        """Health check endpoint for Fly.io and monitoring."""
        return JSONResponse({
            "status": "healthy",
            "service": "flightfinder-mcp",
            "ui_available": is_ui_available(),
            "ui_views": list_available_views() if is_ui_available() else [],
        })

    # Create Starlette app
    routes = [
        Route("/mcp", handle_mcp, methods=["POST"]),
        Route("/health", health_check, methods=["GET"]),
    ]

    app = Starlette(routes=routes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Run server
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)

    print(f"\n🛫 FlightFinder MCP HTTP Server")
    print(f"   Listening on http://localhost:{port}/mcp")
    print(f"\n📡 To use with Claude Desktop:")
    print(f"   1. In another terminal: npx cloudflared tunnel --url http://localhost:{port}")
    print(f"   2. Copy the https://...trycloudflare.com URL")
    print(f"   3. Add as Custom Connector in Claude Desktop Settings > Connectors")
    print(f"\n🎨 MCP Apps UI: {'Enabled' if is_ui_available() else 'Disabled (build ui/ first)'}")
    print()

    await server.serve()


def main():
    """Entry point for the HTTP server."""
    import argparse

    parser = argparse.ArgumentParser(description="FlightFinder MCP HTTP Server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})")
    args = parser.parse_args()

    asyncio.run(create_http_server(port=args.port))


if __name__ == "__main__":
    main()
