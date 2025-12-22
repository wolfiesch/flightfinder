#!/usr/bin/env python3
"""
Deal Scanner: Find cheap round-trip flights from Bay Area airports.

Scans multiple departure windows and aggregates the best deals.
"""

import argparse
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from flightfinder import FlightFinder, RoundTrip


# Bay Area airports
BAY_AREA_AIRPORTS = ["SFO", "OAK", "SJC"]


def scan_window(
    finder: FlightFinder,
    origin: str,
    departure_start: date,
    departure_end: date,
    min_days: int,
    max_days: int,
    max_stops: int,
) -> list[RoundTrip]:
    """Scan a single departure window for deals."""
    try:
        return finder.search_roundtrip(
            origin=origin,
            destination="anywhere",
            departure_from=departure_start,
            departure_to=departure_end,
            min_days=min_days,
            max_days=max_days,
            max_stops=max_stops,
            sort_by="PRICE",
            limit=50,
        )
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Scan for cheap round-trip flights from Bay Area"
    )
    parser.add_argument(
        "--min-days", type=int, default=10, help="Minimum trip duration (default: 10)"
    )
    parser.add_argument(
        "--max-days", type=int, default=20, help="Maximum trip duration (default: 20)"
    )
    parser.add_argument(
        "--max-stops", type=int, default=1, help="Maximum stops per leg (default: 1)"
    )
    parser.add_argument(
        "--months", type=int, default=3, help="Months ahead to scan (default: 3)"
    )
    parser.add_argument(
        "--max-price", type=float, help="Maximum base price to display"
    )
    parser.add_argument(
        "--top", type=int, default=30, help="Number of top deals to show (default: 30)"
    )
    parser.add_argument(
        "--airports",
        nargs="+",
        default=BAY_AREA_AIRPORTS,
        help=f"Airports to search from (default: {' '.join(BAY_AREA_AIRPORTS)})",
    )
    parser.add_argument(
        "--filter",
        choices=["all", "domestic", "international"],
        default="all",
        help="Filter by destination type (default: all)",
    )
    parser.add_argument(
        "--sort-by-bag-price",
        action="store_true",
        help="Sort by price including checked bag",
    )
    parser.add_argument(
        "--show-urls",
        action="store_true",
        help="Show booking URLs for displayed flights",
    )

    args = parser.parse_args()
    console = Console()

    filter_label = {
        "all": "All destinations",
        "domestic": "Domestic (US) only",
        "international": "International only",
    }[args.filter]

    console.print("\n[bold blue]✈️  Flight Deal Scanner[/bold blue]")
    console.print(f"[dim]Searching from: {', '.join(args.airports)}[/dim]")
    console.print(f"[dim]Trip duration: {args.min_days}-{args.max_days} days[/dim]")
    console.print(f"[dim]Filter: {filter_label}[/dim]")
    console.print(f"[dim]Scanning next {args.months} months[/dim]\n")

    # Generate departure windows (2-week chunks)
    today = date.today()
    windows = []
    for weeks_ahead in range(2, args.months * 4 + 2, 2):  # Every 2 weeks
        start = today + timedelta(weeks=weeks_ahead)
        end = start + timedelta(days=13)
        windows.append((start, end))

    # Build search tasks
    tasks = []
    for airport in args.airports:
        for start, end in windows:
            tasks.append((airport, start, end))

    console.print(f"[dim]Running {len(tasks)} searches across {len(args.airports)} airports...[/dim]\n")

    all_trips: list[RoundTrip] = []

    with FlightFinder(timeout=60) as finder:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task_id = progress.add_task("Scanning...", total=len(tasks))

            # Use ThreadPoolExecutor for parallel requests
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {}
                for airport, start, end in tasks:
                    future = executor.submit(
                        scan_window,
                        finder,
                        airport,
                        start,
                        end,
                        args.min_days,
                        args.max_days,
                        args.max_stops,
                    )
                    futures[future] = (airport, start)

                for future in as_completed(futures):
                    airport, start = futures[future]
                    try:
                        trips = future.result()
                        all_trips.extend(trips)
                        progress.update(
                            task_id,
                            advance=1,
                            description=f"Scanning {airport} ({start.strftime('%b %d')})... Found {len(all_trips)} total",
                        )
                    except Exception:
                        progress.update(task_id, advance=1)

    # Apply destination filter
    if args.filter == "domestic":
        all_trips = [t for t in all_trips if t.is_domestic]
    elif args.filter == "international":
        all_trips = [t for t in all_trips if t.is_international]

    # Deduplicate by (origin, destination, outbound date, price)
    seen = set()
    unique_trips = []
    for trip in all_trips:
        key = (
            trip.origin,
            trip.destination,
            trip.outbound.departure_time.date(),
            trip.price,
        )
        if key not in seen:
            seen.add(key)
            unique_trips.append(trip)

    # Filter by max price if specified
    if args.max_price:
        unique_trips = [t for t in unique_trips if t.price <= args.max_price]

    # Sort by price (optionally including bag)
    if args.sort_by_bag_price:
        unique_trips.sort(key=lambda t: t.price_with_bag)
    else:
        unique_trips.sort(key=lambda t: t.price)

    if not unique_trips:
        console.print("[yellow]No deals found matching criteria.[/yellow]")
        return

    # Display results
    top_trips = unique_trips[: args.top]

    table = Table(
        title=f"🔥 Top {len(top_trips)} Cheapest Round-Trips ({args.min_days}-{args.max_days} days) - {filter_label}"
    )
    table.add_column("Base", style="green", justify="right")
    table.add_column("+Bag", style="yellow", justify="right")
    table.add_column("$/Day", style="dim", justify="right")
    table.add_column("From", style="white")
    table.add_column("To", style="cyan")
    table.add_column("City", style="cyan")
    table.add_column("Depart", style="white")
    table.add_column("Return", style="white")
    table.add_column("Days", justify="center")
    table.add_column("Dur", style="dim", justify="center")
    table.add_column("Stops", justify="center")
    table.add_column("Airlines", style="magenta", no_wrap=True)

    for trip in top_trips:
        # Stops with layover airports
        out_stops = trip.outbound.stops
        in_stops = trip.inbound.stops
        if out_stops == 0 and in_stops == 0:
            stops_str = "Direct"
        else:
            stops_str = f"{out_stops}/{in_stops}"
            # Add layover airports if any
            layovers = trip.all_layover_airports
            if layovers:
                stops_str += f" {','.join(layovers[:2])}"  # Show max 2

        # Duration (outbound/inbound)
        dur_str = f"{trip.outbound.duration_short}/{trip.inbound.duration_short}"

        # Departure dates with times
        out_date = trip.outbound.departure_time.strftime("%b %d")
        out_time = trip.outbound.departure_time_short
        in_date = trip.inbound.departure_time.strftime("%b %d")
        in_time = trip.inbound.departure_time_short

        # Airlines (truncate if too many)
        airlines = trip.all_carriers
        if len(airlines) > 2:
            airlines_str = ", ".join(airlines[:2]) + "…"
        else:
            airlines_str = ", ".join(airlines) if airlines else "-"

        # Prices
        bag_price_str = f"${trip.price_with_bag:.0f}" if trip.checked_bag_price else "-"
        ppd_str = f"${trip.price_per_day:.0f}"

        # Location
        city_str = trip.destination_city or ""
        country_str = f" ({trip.destination_country})" if trip.destination_country else ""

        table.add_row(
            f"${trip.price:.0f}",
            bag_price_str,
            ppd_str,
            trip.origin,
            trip.destination,
            f"{city_str}{country_str}",
            f"{out_date} {out_time}",
            f"{in_date} {in_time}",
            str(trip.trip_days),
            dur_str,
            stops_str,
            airlines_str,
        )

    console.print(table)

    # Show booking URLs if requested
    if args.show_urls:
        console.print("\n[bold]Booking URLs:[/bold]")
        base_url = "https://www.kiwi.com"
        for i, trip in enumerate(top_trips[:10], 1):  # Limit to first 10
            if trip.booking_url:
                dest_label = trip.destination_city or trip.destination
                full_url = trip.booking_url if trip.booking_url.startswith("http") else f"{base_url}{trip.booking_url}"
                console.print(
                    f"  {i}. [cyan]{trip.origin}→{dest_label}[/cyan] "
                    f"({trip.outbound.departure_time.strftime('%b %d')} - "
                    f"{trip.inbound.departure_time.strftime('%b %d')}):"
                )
                console.print(f"     [link={full_url}]{full_url}[/link]")
        if len(top_trips) > 10:
            console.print(f"  [dim]...and {len(top_trips) - 10} more[/dim]")

    # Summary by destination
    dest_prices: dict[str, tuple[float, str, str]] = {}  # dest -> (min_price, city, country)
    for trip in unique_trips:
        dest = trip.destination
        if dest not in dest_prices or trip.price < dest_prices[dest][0]:
            dest_prices[dest] = (trip.price, trip.destination_city or "", trip.destination_country or "")

    console.print("\n[bold]Best base price by destination:[/bold]")
    sorted_dests = sorted(dest_prices.items(), key=lambda x: x[1][0])
    for dest, (price, city, country) in sorted_dests[:20]:
        country_str = f" ({country})" if country else ""
        city_str = city if city else dest
        console.print(f"  {city_str}{country_str}: [green]${price:.0f}[/green]")

    console.print(f"\n[dim]Total unique trips found: {len(unique_trips)}[/dim]\n")


if __name__ == "__main__":
    main()
