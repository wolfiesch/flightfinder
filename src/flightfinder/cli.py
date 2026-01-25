"""Enhanced CLI for FlightFinder with multiple commands and export options."""

import argparse
import csv
import json
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

from rich.console import Console
from rich.table import Table

from flightfinder.client import FlightFinder
from flightfinder.config import get_config
from flightfinder.discord import DiscordNotifier
from flightfinder.exceptions import FlightFinderError
from flightfinder.hotel_client import HotelFinder
from flightfinder.hotel_models import LOCATION_KEYS


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="flights",
        description="Search for flights using FlightFinder",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Search command (one-way)
    search_parser = subparsers.add_parser("search", help="Search for one-way flights")
    _add_common_args(search_parser)
    search_parser.add_argument(
        "--min-price", type=float, help="Minimum price filter"
    )

    # Round-trip command
    roundtrip_parser = subparsers.add_parser("roundtrip", help="Search for round-trip flights")
    _add_common_args(roundtrip_parser)
    roundtrip_parser.add_argument(
        "--min-days", type=int, default=7, help="Minimum trip duration (default: 7)"
    )
    roundtrip_parser.add_argument(
        "--max-days", type=int, default=14, help="Maximum trip duration (default: 14)"
    )
    roundtrip_parser.add_argument(
        "--return-from", type=int, help="Days from now for earliest return"
    )
    roundtrip_parser.add_argument(
        "--return-to", type=int, help="Days from now for latest return"
    )

    # Location search command
    location_parser = subparsers.add_parser("location", help="Search for airport/city codes")
    location_parser.add_argument("query", help="Location search query")
    location_parser.add_argument(
        "--type",
        choices=["AIRPORT", "CITY", "COUNTRY"],
        help="Filter by location type",
    )
    location_parser.add_argument(
        "--limit", type=int, default=10, help="Maximum results (default: 10)"
    )
    location_parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )

    # REPL command
    subparsers.add_parser("repl", help="Start interactive REPL mode")

    # Hotels command
    hotels_parser = subparsers.add_parser("hotels", help="Search for hotels")
    hotels_parser.add_argument("location", help="City name (e.g., 'New York') or location key (e.g., 'g60763')")
    hotels_parser.add_argument(
        "--limit", type=int, default=20, help="Number of results (default: 20)"
    )
    hotels_parser.add_argument(
        "--min-price", type=float, help="Minimum nightly price filter"
    )
    hotels_parser.add_argument(
        "--max-price", type=float, help="Maximum nightly price filter"
    )
    hotels_parser.add_argument(
        "--min-rating", type=float, help="Minimum rating filter (0-5)"
    )
    hotels_parser.add_argument(
        "--type",
        choices=["Hotel", "Hostel", "Motel", "Resort", "Ryokan", "B&B"],
        help="Accommodation type filter",
    )
    hotels_parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    hotels_parser.add_argument(
        "--output", "-o", type=str, help="Output file path (defaults to stdout)"
    )
    hotels_parser.add_argument(
        "--discord", action="store_true", help="Send results to Discord webhook"
    )

    # Hotel locations command (list supported cities)
    subparsers.add_parser("hotel-locations", help="List supported hotel search locations")

    # MCP server command
    subparsers.add_parser("mcp-server", help="Start MCP server for AI agent integration")

    # Trip command (combined flight + hotel search)
    trip_parser = subparsers.add_parser("trip", help="Search flights AND hotels together")
    trip_parser.add_argument("origin", help="Origin airport code (e.g., SFO)")
    trip_parser.add_argument("destination", help="Destination city (e.g., 'tokyo', 'new york')")
    trip_parser.add_argument(
        "--days", type=int, default=30, help="Days from now to depart (default: 30)"
    )
    trip_parser.add_argument(
        "--nights", type=int, default=7, help="Number of nights to stay (default: 7)"
    )
    trip_parser.add_argument(
        "--max-price", type=float, help="Maximum flight price filter"
    )
    trip_parser.add_argument(
        "--max-hotel-price", type=float, help="Maximum hotel price per night"
    )
    trip_parser.add_argument(
        "--max-stops", type=int, default=1, help="Maximum flight stops (default: 1)"
    )
    trip_parser.add_argument(
        "--limit", type=int, default=5, help="Results per category (default: 5)"
    )
    trip_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    trip_parser.add_argument(
        "--discord", action="store_true", help="Send results to Discord webhook"
    )

    return parser


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add common arguments to search parsers."""
    parser.add_argument("origin", help="Origin airport code (e.g., SFO)")
    parser.add_argument(
        "-d", "--destination", default="anywhere", help="Destination (default: anywhere)"
    )
    parser.add_argument(
        "--days", type=int, default=30, help="Days from now to start search (default: 30)"
    )
    parser.add_argument(
        "--window", type=int, default=7, help="Search window in days (default: 7)"
    )
    parser.add_argument(
        "--max-stops", type=int, default=1, help="Maximum stops (default: 1)"
    )
    parser.add_argument("--max-price", type=float, help="Maximum price filter")
    parser.add_argument(
        "--limit", type=int, default=20, help="Number of results (default: 20)"
    )
    parser.add_argument(
        "--sort",
        choices=["PRICE", "DURATION", "QUALITY"],
        default="PRICE",
        help="Sort order (default: PRICE)",
    )
    parser.add_argument(
        "--cabin",
        choices=["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"],
        default="ECONOMY",
        help="Cabin class (default: ECONOMY)",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--output", "-o", type=str, help="Output file path (defaults to stdout)"
    )
    parser.add_argument(
        "--discord", action="store_true", help="Send results to Discord webhook"
    )


def cmd_search(args: argparse.Namespace, console: Console) -> int:
    """Execute one-way flight search."""
    departure_from = date.today() + timedelta(days=args.days)
    departure_to = departure_from + timedelta(days=args.window)

    if args.format == "table":
        console.print(f"\n[bold]Searching: {args.origin} → {args.destination}[/bold]")
        console.print(f"[dim]Dates: {departure_from} to {departure_to}[/dim]\n")

    try:
        with FlightFinder() as finder:
            flights = finder.search_flights(
                origin=args.origin,
                destination=args.destination,
                departure_from=departure_from,
                departure_to=departure_to,
                max_stops=args.max_stops,
                max_price=args.max_price,
                min_price=getattr(args, "min_price", None),
                sort_by=args.sort,
                limit=args.limit,
                cabin_class=args.cabin,
            )

            if not flights:
                console.print("[yellow]No flights found.[/yellow]")
                return 0

            _output_flights(flights, args, console)

            # Send to Discord if requested
            if getattr(args, "discord", False):
                _send_flights_to_discord(flights, args.origin, args.destination, console)

            return 0

    except FlightFinderError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def cmd_roundtrip(args: argparse.Namespace, console: Console) -> int:
    """Execute round-trip flight search."""
    departure_from = date.today() + timedelta(days=args.days)
    departure_to = departure_from + timedelta(days=args.window)

    return_from = None
    return_to = None
    if args.return_from:
        return_from = date.today() + timedelta(days=args.return_from)
    if args.return_to:
        return_to = date.today() + timedelta(days=args.return_to)

    if args.format == "table":
        console.print(f"\n[bold]Round-trip: {args.origin} → {args.destination}[/bold]")
        console.print(f"[dim]Outbound: {departure_from} to {departure_to}[/dim]")
        console.print(f"[dim]Trip duration: {args.min_days}-{args.max_days} days[/dim]\n")

    try:
        with FlightFinder() as finder:
            roundtrips = finder.search_roundtrip(
                origin=args.origin,
                destination=args.destination,
                departure_from=departure_from,
                departure_to=departure_to,
                return_from=return_from,
                return_to=return_to,
                min_days=args.min_days,
                max_days=args.max_days,
                max_stops=args.max_stops,
                max_price=args.max_price,
                sort_by=args.sort,
                limit=args.limit,
                cabin_class=args.cabin,
            )

            if not roundtrips:
                console.print("[yellow]No round-trip flights found.[/yellow]")
                return 0

            _output_roundtrips(roundtrips, args, console)

            # Send to Discord if requested
            if getattr(args, "discord", False):
                _send_roundtrips_to_discord(roundtrips, args.origin, args.destination, console)

            return 0

    except FlightFinderError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def cmd_location(args: argparse.Namespace, console: Console) -> int:
    """Execute location search."""
    location_types = [args.type] if args.type else None

    try:
        with FlightFinder() as finder:
            locations = finder.find_location(
                term=args.query,
                location_types=location_types,
                limit=args.limit,
            )

            if not locations:
                console.print("[yellow]No locations found.[/yellow]")
                return 0

            _output_locations(locations, args, console)
            return 0

    except FlightFinderError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def cmd_repl(console: Console) -> int:
    """Start interactive REPL mode."""
    console.print("\n[bold]FlightFinder Interactive Mode[/bold]")
    console.print("[dim]Type 'help' for commands, 'quit' to exit[/dim]\n")

    finder = FlightFinder()

    while True:
        try:
            user_input = input("flights> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        parts = user_input.split()
        cmd = parts[0].lower()

        if cmd in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break

        elif cmd == "help":
            console.print("""
[bold]Available commands:[/bold]
  search <origin> [destination]  - Search one-way flights
  roundtrip <origin> [dest]      - Search round-trip flights
  hotels <city>                  - Search for hotels
  trip <origin> <dest>           - Search flights + hotels together
  location <query>               - Search for airport codes
  cache                          - Show cache statistics
  clear                          - Clear response cache
  quit                           - Exit REPL
""")

        elif cmd == "search" and len(parts) >= 2:
            origin = parts[1]
            dest = parts[2] if len(parts) > 2 else "anywhere"
            try:
                flights = finder.search_flights(
                    origin=origin,
                    destination=dest,
                    departure_from=date.today() + timedelta(days=30),
                    departure_to=date.today() + timedelta(days=37),
                    limit=10,
                )
                if flights:
                    table = Table(title=f"Flights from {origin}")
                    table.add_column("Price", style="green", justify="right")
                    table.add_column("To", style="cyan")
                    table.add_column("Date")
                    table.add_column("Duration", justify="right")
                    table.add_column("Stops", justify="center")

                    for flight in flights[:10]:
                        table.add_row(
                            f"${flight.price:.0f}",
                            flight.destination,
                            flight.departure_time.strftime("%b %d"),
                            flight.duration_formatted,
                            flight.stops_label,
                        )
                    console.print(table)
                else:
                    console.print("[yellow]No flights found.[/yellow]")
            except FlightFinderError as e:
                console.print(f"[red]Error: {e}[/red]")

        elif cmd == "roundtrip" and len(parts) >= 2:
            origin = parts[1]
            dest = parts[2] if len(parts) > 2 else "anywhere"
            try:
                roundtrips = finder.search_roundtrip(
                    origin=origin,
                    destination=dest,
                    departure_from=date.today() + timedelta(days=30),
                    departure_to=date.today() + timedelta(days=37),
                    min_days=7,
                    max_days=14,
                    limit=10,
                )
                if roundtrips:
                    table = Table(title=f"Round-trips from {origin}")
                    table.add_column("Price", style="green", justify="right")
                    table.add_column("To", style="cyan")
                    table.add_column("Dates")
                    table.add_column("Days", justify="center")
                    table.add_column("Stops", justify="center")

                    for rt in roundtrips[:10]:
                        out_date = rt.outbound.departure_time.strftime("%b %d")
                        in_date = rt.inbound.departure_time.strftime("%b %d")
                        table.add_row(
                            f"${rt.price:.0f}",
                            rt.destination,
                            f"{out_date} - {in_date}",
                            str(rt.trip_days),
                            f"{rt.outbound.stops}/{rt.inbound.stops}",
                        )
                    console.print(table)
                else:
                    console.print("[yellow]No round-trips found.[/yellow]")
            except FlightFinderError as e:
                console.print(f"[red]Error: {e}[/red]")

        elif cmd == "location" and len(parts) >= 2:
            query = " ".join(parts[1:])
            try:
                locations = finder.find_location(query, limit=10)
                if locations:
                    table = Table(title="Locations")
                    table.add_column("Code", style="cyan")
                    table.add_column("Name")
                    table.add_column("Type")
                    table.add_column("City")
                    table.add_column("Country")

                    for loc in locations:
                        table.add_row(
                            loc.id,
                            loc.name,
                            loc.type,
                            loc.city or "",
                            loc.country or "",
                        )
                    console.print(table)
                else:
                    console.print("[yellow]No locations found.[/yellow]")
            except FlightFinderError as e:
                console.print(f"[red]Error: {e}[/red]")

        elif cmd == "hotels" and len(parts) >= 2:
            location = " ".join(parts[1:])
            try:
                with HotelFinder() as hotel_finder:
                    results = hotel_finder.search_hotels(location, limit=10)
                    if results.hotels:
                        table = Table(title=f"Hotels in {location}")
                        table.add_column("Price", style="green", justify="right")
                        table.add_column("Name", max_width=30)
                        table.add_column("Rating", justify="center")
                        table.add_column("Type")

                        for hotel in results.hotels[:10]:
                            price_str = f"${hotel.min_price:.0f}" if hotel.min_price else "N/A"
                            rating_str = f"{hotel.rating:.1f}/5" if hotel.rating else "N/A"
                            table.add_row(
                                price_str,
                                hotel.name[:30],
                                rating_str,
                                hotel.accommodation_type,
                            )
                        console.print(table)
                    else:
                        console.print("[yellow]No hotels found.[/yellow]")
            except FlightFinderError as e:
                console.print(f"[red]Error: {e}[/red]")

        elif cmd == "trip" and len(parts) >= 3:
            origin = parts[1]
            dest = " ".join(parts[2:])
            try:
                console.print(f"[dim]Searching flights {origin} → {dest}...[/dim]")
                roundtrips = finder.search_roundtrip(
                    origin=origin,
                    destination=dest,
                    departure_from=date.today() + timedelta(days=30),
                    departure_to=date.today() + timedelta(days=37),
                    min_days=7,
                    max_days=10,
                    limit=5,
                )

                hotels = []
                from flightfinder.hotel_models import get_location_key
                hotel_location = get_location_key(dest)
                if hotel_location:
                    console.print(f"[dim]Searching hotels in {dest}...[/dim]")
                    with HotelFinder() as hotel_finder:
                        results = hotel_finder.search_hotels(hotel_location, limit=5)
                        hotels = results.hotels

                if roundtrips:
                    table = Table(title=f"Flights: {origin} → {dest}")
                    table.add_column("Price", style="green", justify="right")
                    table.add_column("Dates")
                    table.add_column("Days", justify="center")

                    for rt in roundtrips[:5]:
                        out_date = rt.outbound.departure_time.strftime("%b %d")
                        in_date = rt.inbound.departure_time.strftime("%b %d")
                        table.add_row(
                            f"${rt.price:.0f}",
                            f"{out_date} - {in_date}",
                            str(rt.trip_days),
                        )
                    console.print(table)

                if hotels:
                    table = Table(title=f"Hotels in {dest}")
                    table.add_column("Price", style="green", justify="right")
                    table.add_column("Name", max_width=25)
                    table.add_column("Rating", justify="center")

                    for hotel in hotels[:5]:
                        price_str = f"${hotel.min_price:.0f}" if hotel.min_price else "N/A"
                        rating_str = f"{hotel.rating:.1f}/5" if hotel.rating else "N/A"
                        table.add_row(price_str, hotel.name[:25], rating_str)
                    console.print(table)

                # Summary
                if roundtrips and hotels:
                    min_flight = min(rt.price for rt in roundtrips)
                    min_hotel = min(h.min_price for h in hotels if h.min_price)
                    if min_hotel:
                        total = min_flight + (min_hotel * 7)
                        console.print(f"\n[bold]Estimated 7-night trip: ${total:.0f}[/bold]")

            except FlightFinderError as e:
                console.print(f"[red]Error: {e}[/red]")

        elif cmd == "cache":
            stats = finder.cache_stats()
            if stats:
                console.print(f"Cache stats: {stats}")
            else:
                console.print("[dim]Caching disabled[/dim]")

        elif cmd == "clear":
            cleared = finder.clear_cache()
            console.print(f"[dim]Cleared {cleared} cache entries[/dim]")

        else:
            console.print(f"[yellow]Unknown command: {cmd}. Type 'help' for available commands.[/yellow]")

    finder.close()
    return 0


def cmd_hotels(args: argparse.Namespace, console: Console) -> int:
    """Execute hotel search."""
    if args.format == "table":
        console.print(f"\n[bold]Searching hotels in: {args.location}[/bold]\n")

    try:
        with HotelFinder() as finder:
            accommodation_types = [args.type] if args.type else None
            results = finder.search_hotels(
                location=args.location,
                limit=args.limit,
                min_price=args.min_price,
                max_price=args.max_price,
                min_rating=args.min_rating,
                accommodation_types=accommodation_types,
            )

            if not results.hotels:
                console.print("[yellow]No hotels found.[/yellow]")
                return 0

            _output_hotels(results.hotels, args, console)

            if args.format == "table" and results.has_more:
                console.print(f"\n[dim]Showing {len(results.hotels)} of {results.total_count} total results[/dim]")

            # Send to Discord if requested
            if getattr(args, "discord", False):
                _send_hotels_to_discord(results.hotels, args.location, args, console)

            return 0

    except FlightFinderError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def cmd_trip(args: argparse.Namespace, console: Console) -> int:
    """Execute combined flight + hotel search."""
    from flightfinder.hotel_models import get_location_key

    departure_from = date.today() + timedelta(days=args.days)
    departure_to = departure_from + timedelta(days=7)  # 7-day window

    if args.format == "table":
        console.print(f"\n[bold]Planning trip: {args.origin} → {args.destination}[/bold]")
        console.print(f"[dim]Depart around {departure_from}, stay {args.nights} nights[/dim]\n")

    # Check if destination is a valid hotel location
    hotel_location = args.destination if args.destination.startswith("g") else get_location_key(args.destination)
    if not hotel_location:
        console.print(f"[yellow]Warning: '{args.destination}' is not a known hotel location.[/yellow]")
        console.print("[dim]Use 'flights hotel-locations' to see supported cities.[/dim]\n")
        hotel_location = None

    flights = []
    hotels = []

    try:
        # Search flights
        with FlightFinder() as flight_finder:
            console.print("[dim]Searching flights...[/dim]")
            flights = flight_finder.search_roundtrip(
                origin=args.origin,
                destination=args.destination,
                departure_from=departure_from,
                departure_to=departure_to,
                min_days=args.nights,
                max_days=args.nights + 3,  # Allow some flexibility
                max_stops=args.max_stops,
                max_price=args.max_price,
                limit=args.limit,
            )

        # Search hotels (if location is valid)
        if hotel_location:
            with HotelFinder() as hotel_finder:
                console.print("[dim]Searching hotels...[/dim]")
                results = hotel_finder.search_hotels(
                    location=hotel_location,
                    limit=args.limit,
                    max_price=args.max_hotel_price,
                )
                hotels = results.hotels

        if not flights and not hotels:
            console.print("[yellow]No results found.[/yellow]")
            return 0

        # Output results
        _output_trip(flights, hotels, args, console)

        # Send to Discord if requested
        if getattr(args, "discord", False):
            _send_trip_to_discord(args.origin, args.destination, flights, hotels, args.nights, console)

        return 0

    except FlightFinderError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def _output_trip(flights, hotels, args: argparse.Namespace, console: Console) -> None:
    """Output trip search results."""
    if args.format == "json":
        data = {
            "origin": args.origin,
            "destination": args.destination,
            "nights": args.nights,
            "flights": [
                {
                    "price": f.price,
                    "dates": f"{f.outbound.departure_time.date()} - {f.inbound.departure_time.date()}",
                    "trip_days": f.trip_days,
                    "carriers": f.all_carriers,
                }
                for f in flights
            ],
            "hotels": [
                {
                    "name": h.name,
                    "type": h.accommodation_type,
                    "price_range": str(h.price_range) if h.price_range else None,
                    "rating": h.rating,
                }
                for h in hotels
            ],
        }

        # Calculate estimated total
        if flights and hotels:
            min_flight = min(f.price for f in flights)
            min_hotel = min(h.min_price for h in hotels if h.min_price)
            data["estimated_total"] = min_flight + (min_hotel * args.nights) if min_hotel else None

        console.print(json.dumps(data, indent=2))
        return

    # Table output
    if flights:
        table = Table(title=f"✈️ Round-trip Flights: {args.origin} → {args.destination}")
        table.add_column("Price", style="green", justify="right")
        table.add_column("Dates")
        table.add_column("Days", justify="center")
        table.add_column("Stops", justify="center")
        table.add_column("Airlines")

        for f in flights[:args.limit]:
            out_date = f.outbound.departure_time.strftime("%b %d")
            in_date = f.inbound.departure_time.strftime("%b %d")
            table.add_row(
                f"${f.price:.0f}",
                f"{out_date} - {in_date}",
                str(f.trip_days),
                f"{f.outbound.stops}/{f.inbound.stops}",
                ", ".join(f.all_carriers[:2]),
            )

        console.print(table)
        console.print()

    if hotels:
        table = Table(title=f"🏨 Hotels in {args.destination}")
        table.add_column("Price/Night", style="green", justify="right")
        table.add_column("Name", max_width=30)
        table.add_column("Rating", justify="center")
        table.add_column("Type")

        for h in hotels[:args.limit]:
            price_str = f"${h.min_price:.0f}" if h.min_price else "N/A"
            rating_str = f"{h.rating:.1f}/5" if h.rating else "N/A"
            table.add_row(
                price_str,
                h.name[:30],
                rating_str,
                h.accommodation_type,
            )

        console.print(table)
        console.print()

    # Trip summary
    if flights and hotels:
        min_flight = min(f.price for f in flights)
        hotel_with_price = [h for h in hotels if h.min_price]
        if hotel_with_price:
            min_hotel = min(h.min_price for h in hotel_with_price)
            total_hotel = min_hotel * args.nights
            estimated_total = min_flight + total_hotel

            console.print("[bold]💰 Estimated Trip Cost[/bold]")
            console.print(f"  ✈️ Cheapest flight: ${min_flight:.0f}")
            console.print(f"  🏨 Cheapest hotel: ${min_hotel:.0f}/night × {args.nights} nights = ${total_hotel:.0f}")
            console.print(f"  [green bold]Total: ${estimated_total:.0f}[/green bold]")


def cmd_hotel_locations(console: Console) -> int:
    """List supported hotel search locations."""
    console.print("\n[bold]Supported Hotel Search Locations[/bold]\n")

    # Group by region
    us_cities = []
    intl_cities = []

    for city, key in sorted(LOCATION_KEYS.items()):
        # Simple heuristic: US cities have g3xxxx or g6xxxx keys typically
        if key.startswith("g6") or key.startswith("g3") or key.startswith("g45") or key.startswith("g28"):
            us_cities.append((city.title(), key))
        else:
            intl_cities.append((city.title(), key))

    table = Table(title="United States")
    table.add_column("City", style="cyan")
    table.add_column("Location Key", style="dim")

    for city, key in sorted(us_cities):
        table.add_row(city, key)

    console.print(table)
    console.print()

    table = Table(title="International")
    table.add_column("City", style="cyan")
    table.add_column("Location Key", style="dim")

    for city, key in sorted(intl_cities):
        table.add_row(city, key)

    console.print(table)
    console.print("\n[dim]Use city names directly (e.g., 'flights hotels \"new york\"')[/dim]")
    console.print("[dim]Or use location keys for unsupported cities from TripAdvisor URLs[/dim]")

    return 0


def _output_hotels(hotels, args: argparse.Namespace, console: Console) -> None:
    """Output hotel results in specified format."""
    if args.format == "json":
        data = [
            {
                "key": h.key,
                "name": h.name,
                "type": h.accommodation_type,
                "rating": h.rating,
                "review_count": h.review_count,
                "min_price": h.min_price,
                "max_price": h.max_price,
                "url": h.url,
                "image_url": h.image_url,
                "mentions": h.mentions,
                "labels": h.labels,
                "latitude": h.location.latitude if h.location else None,
                "longitude": h.location.longitude if h.location else None,
            }
            for h in hotels
        ]
        _write_output(json.dumps(data, indent=2), args.output, console)

    elif args.format == "csv":
        output = _hotels_to_csv(hotels)
        _write_output(output, args.output, console)

    else:
        table = Table(title=f"Hotels in {args.location}")
        table.add_column("Price", style="green", justify="right")
        table.add_column("Name", style="cyan", max_width=35)
        table.add_column("Type")
        table.add_column("Rating", justify="center")
        table.add_column("Reviews", justify="right")
        table.add_column("Tags", max_width=25)

        for hotel in hotels:
            price_str = str(hotel.price_range) if hotel.price_range else "N/A"
            rating_str = f"{hotel.rating:.1f}/5" if hotel.rating else "N/A"
            reviews_str = f"{hotel.review_count:,}" if hotel.review_count else ""
            tags = ", ".join(hotel.mentions[:2] + hotel.labels[:1])
            if len(hotel.mentions) + len(hotel.labels) > 3:
                tags += "..."

            table.add_row(
                price_str,
                hotel.name,
                hotel.accommodation_type,
                rating_str,
                reviews_str,
                tags,
            )

        console.print(table)


def _hotels_to_csv(hotels) -> str:
    """Convert hotels to CSV string."""
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "key", "name", "type", "rating", "review_count",
        "min_price", "max_price", "url", "mentions"
    ])
    for h in hotels:
        writer.writerow([
            h.key,
            h.name,
            h.accommodation_type,
            h.rating or "",
            h.review_count or "",
            h.min_price or "",
            h.max_price or "",
            h.url or "",
            "|".join(h.mentions),
        ])
    return output.getvalue()


def _output_flights(flights, args: argparse.Namespace, console: Console) -> None:
    """Output flight results in specified format."""
    if args.format == "json":
        data = [
            {
                "price": f.price,
                "origin": f.origin,
                "destination": f.destination,
                "departure_time": f.departure_time.isoformat(),
                "arrival_time": f.arrival_time.isoformat(),
                "duration_minutes": f.duration_minutes,
                "stops": f.stops,
                "carriers": f.carriers,
                "booking_url": f.deep_link,
            }
            for f in flights
        ]
        _write_output(json.dumps(data, indent=2), args.output, console)

    elif args.format == "csv":
        output = _flights_to_csv(flights)
        _write_output(output, args.output, console)

    else:
        table = Table(title=f"Flights from {args.origin}")
        table.add_column("Price", style="green", justify="right")
        table.add_column("To", style="cyan")
        table.add_column("Date")
        table.add_column("Time")
        table.add_column("Duration", justify="right")
        table.add_column("Stops", justify="center")
        table.add_column("Carrier")

        for flight in flights:
            carriers = ", ".join(flight.carriers[:2])
            if len(flight.carriers) > 2:
                carriers += "..."
            table.add_row(
                f"${flight.price:.0f}",
                flight.destination,
                flight.departure_time.strftime("%b %d"),
                flight.departure_time.strftime("%H:%M"),
                flight.duration_formatted,
                flight.stops_label,
                carriers,
            )

        console.print(table)


def _output_roundtrips(roundtrips, args: argparse.Namespace, console: Console) -> None:
    """Output round-trip results in specified format."""
    if args.format == "json":
        data = [
            {
                "price": rt.price,
                "price_with_bag": rt.price_with_bag,
                "origin": rt.origin,
                "destination": rt.destination,
                "destination_city": rt.destination_city,
                "destination_country": rt.destination_country,
                "outbound_date": rt.outbound.departure_time.isoformat(),
                "inbound_date": rt.inbound.departure_time.isoformat(),
                "trip_days": rt.trip_days,
                "outbound_stops": rt.outbound.stops,
                "inbound_stops": rt.inbound.stops,
                "carriers": rt.all_carriers,
                "booking_url": rt.booking_url,
            }
            for rt in roundtrips
        ]
        _write_output(json.dumps(data, indent=2), args.output, console)

    elif args.format == "csv":
        output = _roundtrips_to_csv(roundtrips)
        _write_output(output, args.output, console)

    else:
        table = Table(title=f"Round-trips from {args.origin}")
        table.add_column("Price", style="green", justify="right")
        table.add_column("To", style="cyan")
        table.add_column("Dates")
        table.add_column("Days", justify="center")
        table.add_column("Out", justify="center")
        table.add_column("Return", justify="center")
        table.add_column("Carrier")

        for rt in roundtrips:
            out_date = rt.outbound.departure_time.strftime("%b %d")
            in_date = rt.inbound.departure_time.strftime("%b %d")
            carriers = ", ".join(rt.all_carriers[:2])
            if len(rt.all_carriers) > 2:
                carriers += "..."

            bag_str = ""
            if rt.checked_bag_price:
                bag_str = f" (+${rt.checked_bag_price:.0f})"

            table.add_row(
                f"${rt.price:.0f}{bag_str}",
                f"{rt.destination} ({rt.destination_city or ''})",
                f"{out_date} - {in_date}",
                str(rt.trip_days),
                rt.outbound.stops_label,
                rt.inbound.stops_label,
                carriers,
            )

        console.print(table)


def _output_locations(locations, args: argparse.Namespace, console: Console) -> None:
    """Output location results in specified format."""
    if args.format == "json":
        data = [
            {
                "id": loc.id,
                "name": loc.name,
                "type": loc.type,
                "city": loc.city,
                "country": loc.country,
                "country_code": loc.country_code,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
            }
            for loc in locations
        ]
        _write_output(json.dumps(data, indent=2), None, console)

    elif args.format == "csv":
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "type", "city", "country", "country_code"])
        for loc in locations:
            writer.writerow([loc.id, loc.name, loc.type, loc.city or "", loc.country or "", loc.country_code or ""])
        _write_output(output.getvalue(), None, console)

    else:
        table = Table(title="Locations")
        table.add_column("Code", style="cyan")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("City")
        table.add_column("Country")

        for loc in locations:
            table.add_row(
                loc.id,
                loc.name,
                loc.type,
                loc.city or "",
                loc.country or "",
            )

        console.print(table)


def _flights_to_csv(flights) -> str:
    """Convert flights to CSV string."""
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "price", "origin", "destination", "departure_date", "departure_time",
        "duration", "stops", "carriers"
    ])
    for f in flights:
        writer.writerow([
            f.price,
            f.origin,
            f.destination,
            f.departure_time.strftime("%Y-%m-%d"),
            f.departure_time.strftime("%H:%M"),
            f.duration_formatted,
            f.stops,
            "|".join(f.carriers),
        ])
    return output.getvalue()


def _roundtrips_to_csv(roundtrips) -> str:
    """Convert round-trips to CSV string."""
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "price", "price_with_bag", "origin", "destination", "destination_city",
        "outbound_date", "inbound_date", "trip_days", "outbound_stops",
        "inbound_stops", "carriers"
    ])
    for rt in roundtrips:
        writer.writerow([
            rt.price,
            rt.price_with_bag,
            rt.origin,
            rt.destination,
            rt.destination_city or "",
            rt.outbound.departure_time.strftime("%Y-%m-%d"),
            rt.inbound.departure_time.strftime("%Y-%m-%d"),
            rt.trip_days,
            rt.outbound.stops,
            rt.inbound.stops,
            "|".join(rt.all_carriers),
        ])
    return output.getvalue()


def _write_output(content: str, output_path: str | None, console: Console) -> None:
    """Write content to file or stdout."""
    if output_path:
        Path(output_path).write_text(content)
        console.print(f"[dim]Output written to {output_path}[/dim]")
    else:
        console.print(content)


def _send_flights_to_discord(flights, origin: str, destination: str, console: Console) -> None:
    """Send flight results to Discord webhook."""
    config = get_config()
    webhook_url = config.discord.webhook_url

    if not webhook_url:
        console.print("[yellow]Discord webhook URL not configured. Set it in ~/.flightfinder/config.json[/yellow]")
        return

    console.print(f"\n[bold]Sending {len(flights)} flights to Discord...[/bold]")

    try:
        with DiscordNotifier(webhook_url=webhook_url) as notifier:
            sent = notifier.send_search_results(origin, destination, flights)
            console.print(f"[green]Sent {sent} flights to Discord[/green]")
    except Exception as e:
        console.print(f"[red]Error sending to Discord: {e}[/red]")


def _send_roundtrips_to_discord(roundtrips, origin: str, destination: str, console: Console) -> None:
    """Send round-trip results to Discord webhook."""
    config = get_config()
    webhook_url = config.discord.webhook_url

    if not webhook_url:
        console.print("[yellow]Discord webhook URL not configured. Set it in ~/.flightfinder/config.json[/yellow]")
        return

    console.print(f"\n[bold]Sending {len(roundtrips)} round-trips to Discord...[/bold]")

    try:
        with DiscordNotifier(webhook_url=webhook_url) as notifier:
            sent = notifier.send_search_results(origin, destination, roundtrips)
            console.print(f"[green]Sent {sent} round-trips to Discord[/green]")
    except Exception as e:
        console.print(f"[red]Error sending to Discord: {e}[/red]")


def _send_hotels_to_discord(hotels, location: str, args: argparse.Namespace, console: Console) -> None:
    """Send hotel results to Discord webhook."""
    config = get_config()
    webhook_url = config.discord.webhook_url

    if not webhook_url:
        console.print("[yellow]Discord webhook URL not configured. Set it in ~/.flightfinder/config.json[/yellow]")
        return

    console.print(f"\n[bold]Sending {len(hotels)} hotels to Discord...[/bold]")

    search_params = {}
    if hasattr(args, "min_price") and args.min_price:
        search_params["min_price"] = args.min_price
    if hasattr(args, "max_price") and args.max_price:
        search_params["max_price"] = args.max_price
    if hasattr(args, "min_rating") and args.min_rating:
        search_params["min_rating"] = args.min_rating
    if hasattr(args, "type") and args.type:
        search_params["type"] = args.type

    try:
        with DiscordNotifier(webhook_url=webhook_url) as notifier:
            sent = notifier.send_hotel_results(location, hotels, search_params)
            console.print(f"[green]Sent {sent} hotels to Discord[/green]")
    except Exception as e:
        console.print(f"[red]Error sending to Discord: {e}[/red]")


def _send_trip_to_discord(origin: str, destination: str, flights, hotels, nights: int, console: Console) -> None:
    """Send trip summary to Discord webhook."""
    config = get_config()
    webhook_url = config.discord.webhook_url

    if not webhook_url:
        console.print("[yellow]Discord webhook URL not configured. Set it in ~/.flightfinder/config.json[/yellow]")
        return

    console.print("\n[bold]Sending trip summary to Discord...[/bold]")

    try:
        with DiscordNotifier(webhook_url=webhook_url) as notifier:
            # Send trip summary
            notifier.send_trip_summary(origin, destination, flights, hotels, nights)

            # Optionally send top flights and hotels
            if flights:
                console.print(f"[dim]Sending top {min(3, len(flights))} flights...[/dim]")
                for f in sorted(flights, key=lambda x: x.price)[:3]:
                    notifier.send_roundtrip(f, f"Trip: {origin} → {destination}")

            if hotels:
                console.print(f"[dim]Sending top {min(3, len(hotels))} hotels...[/dim]")
                for h in sorted(hotels, key=lambda x: x.min_price or 999999)[:3]:
                    notifier.send_hotel(h, f"Hotels in {destination}")

            console.print("[green]Trip summary sent to Discord[/green]")
    except Exception as e:
        console.print(f"[red]Error sending to Discord: {e}[/red]")


def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    console = Console()

    setup_logging(args.verbose)

    # Default to search if origin provided without subcommand (backward compat)
    if args.command is None:
        # Check if first positional arg looks like an airport code
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            # Legacy mode: treat as search command
            search_parser = argparse.ArgumentParser()
            _add_common_args(search_parser)
            search_parser.add_argument("--min-price", type=float)
            search_parser.add_argument("-v", "--verbose", action="store_true")
            args = search_parser.parse_args()
            setup_logging(args.verbose)
            return cmd_search(args, console)
        else:
            parser.print_help()
            return 0

    if args.command == "search":
        return cmd_search(args, console)
    elif args.command == "roundtrip":
        return cmd_roundtrip(args, console)
    elif args.command == "location":
        return cmd_location(args, console)
    elif args.command == "repl":
        return cmd_repl(console)
    elif args.command == "hotels":
        return cmd_hotels(args, console)
    elif args.command == "hotel-locations":
        return cmd_hotel_locations(console)
    elif args.command == "trip":
        return cmd_trip(args, console)
    elif args.command == "mcp-server":
        return cmd_mcp_server(console)
    else:
        parser.print_help()
        return 0


def cmd_mcp_server(console: Console) -> int:
    """Start the MCP server for AI agent integration."""
    try:
        import asyncio

        from flightfinder.mcp_server import main as mcp_main
        asyncio.run(mcp_main())
        return 0
    except ImportError:
        console.print("[red]Error: MCP support requires the 'mcp' package.[/red]")
        console.print("[dim]Install with: pip install flightfinder[mcp][/dim]")
        return 1
    except Exception as e:
        console.print(f"[red]Error starting MCP server: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
