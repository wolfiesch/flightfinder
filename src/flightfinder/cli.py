"""Simple CLI for FlightFinder."""

import argparse
from datetime import date, timedelta
from rich.console import Console
from rich.table import Table
from flightfinder.client import FlightFinder


def main():
    parser = argparse.ArgumentParser(description="Search for flights")
    parser.add_argument("origin", help="Origin airport code (e.g., SFO)")
    parser.add_argument(
        "--destination", "-d", default="anywhere", help="Destination (default: anywhere)"
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
    parser.add_argument(
        "--max-price", type=float, help="Maximum price filter"
    )
    parser.add_argument(
        "--limit", type=int, default=20, help="Number of results (default: 20)"
    )
    parser.add_argument(
        "--sort", choices=["PRICE", "DURATION", "QUALITY"], default="PRICE"
    )

    args = parser.parse_args()
    console = Console()

    departure_from = date.today() + timedelta(days=args.days)
    departure_to = departure_from + timedelta(days=args.window)

    console.print(f"\n[bold]Searching: {args.origin} → {args.destination}[/bold]")
    console.print(f"[dim]Dates: {departure_from} to {departure_to}[/dim]\n")

    with FlightFinder() as finder:
        flights = finder.search_flights(
            origin=args.origin,
            destination=args.destination,
            departure_from=departure_from,
            departure_to=departure_to,
            max_stops=args.max_stops,
            max_price=args.max_price,
            sort_by=args.sort,
            limit=args.limit,
        )

        if not flights:
            console.print("[yellow]No flights found.[/yellow]")
            return

        table = Table(title=f"Flights from {args.origin}")
        table.add_column("Price", style="green", justify="right")
        table.add_column("To", style="cyan")
        table.add_column("Date")
        table.add_column("Time")
        table.add_column("Duration", justify="right")
        table.add_column("Stops", justify="center")

        for flight in flights:
            table.add_row(
                f"${flight.price:.0f}",
                flight.destination,
                flight.departure_time.strftime("%b %d"),
                flight.departure_time.strftime("%H:%M"),
                flight.duration_formatted,
                flight.stops_label,
            )

        console.print(table)


if __name__ == "__main__":
    main()
