#!/usr/bin/env python3
"""
Example: Search for flights from SF Bay Area to anywhere.

This script demonstrates how to use FlightFinder to search for
flexible travel options departing from SFO, OAK, or SJC.
"""

from datetime import date, timedelta
from rich.console import Console
from rich.table import Table
from flightfinder import FlightFinder


def main():
    console = Console()

    # Bay Area airports
    bay_area_airports = ["SFO", "OAK", "SJC"]

    console.print("\n[bold blue]FlightFinder - Bay Area Departure Search[/bold blue]\n")

    with FlightFinder() as finder:
        # Verify the airport codes
        console.print("[dim]Finding Bay Area airports...[/dim]")
        for code in bay_area_airports:
            locations = finder.find_location(code)
            if locations:
                console.print(f"  [green]✓[/green] {locations[0]}")

        console.print()

        # Search parameters
        search_start = date.today() + timedelta(days=30)  # 1 month from now
        search_end = search_start + timedelta(days=14)  # 2 week window

        console.print(
            f"[bold]Searching flights from SFO to anywhere[/bold]\n"
            f"  Dates: {search_start} to {search_end}\n"
            f"  Max stops: 1\n"
        )

        flights = finder.search_flights(
            origin="SFO",
            destination="anywhere",
            departure_from=search_start,
            departure_to=search_end,
            max_stops=1,
            sort_by="PRICE",
            limit=25,
        )

        if not flights:
            console.print("[yellow]No flights found. Try adjusting search parameters.[/yellow]")
            return

        # Display results in a table
        table = Table(title=f"Top {len(flights)} Cheapest Flights from SFO")
        table.add_column("Price", style="green", justify="right")
        table.add_column("Destination", style="cyan")
        table.add_column("Date", style="white")
        table.add_column("Duration", justify="right")
        table.add_column("Stops", justify="center")
        table.add_column("Airlines")

        for flight in flights:
            airlines = ", ".join(set(s.carrier for s in flight.segments if s.carrier))
            table.add_row(
                f"${flight.price:.0f}",
                flight.destination,
                flight.departure_time.strftime("%b %d %H:%M"),
                flight.duration_formatted,
                flight.stops_label,
                airlines or "N/A",
            )

        console.print(table)

        # Show unique destinations
        destinations = sorted(set(f.destination for f in flights))
        console.print(f"\n[dim]Unique destinations found: {len(destinations)}[/dim]")
        console.print(f"[dim]{', '.join(destinations)}[/dim]\n")


if __name__ == "__main__":
    main()
