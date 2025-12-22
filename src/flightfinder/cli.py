"""Enhanced CLI for FlightFinder with multiple commands and export options."""

import argparse
import csv
import json
import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from flightfinder.client import FlightFinder
from flightfinder.config import get_config
from flightfinder.discord import DiscordNotifier
from flightfinder.exceptions import FlightFinderError


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


def _write_output(content: str, output_path: Optional[str], console: Console) -> None:
    """Write content to file or stdout."""
    if output_path:
        Path(output_path).write_text(content)
        console.print(f"[dim]Output written to {output_path}[/dim]")
    else:
        console.print(content)


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
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
