# FlightFinder

A Python client for searching flights via the Kiwi/Skypicker GraphQL API. No API key required.

## Features

- **One-way and round-trip flight search**
- **"Anywhere" destination search** - find the cheapest flights to any destination
- **Location search** - find airport codes by name
- **Async support** - concurrent searches with `AsyncFlightFinder`
- **Response caching** - reduce API calls with automatic caching
- **Retry logic** - exponential backoff for transient failures
- **Rate limit handling** - graceful handling of API rate limits
- **Deal alerts** - set price alerts for routes you're watching
- **Multiple output formats** - table, JSON, CSV export
- **Interactive REPL** - explore flights interactively

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/flightfinder.git
cd flightfinder

# Create virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick Start

### Python API

```python
from flightfinder import FlightFinder
from datetime import date, timedelta

# Search for flights
with FlightFinder() as finder:
    # One-way search
    flights = finder.search_flights(
        origin="SFO",
        destination="LAX",
        departure_from=date.today() + timedelta(days=30),
        max_stops=1,
        limit=10,
    )

    for flight in flights:
        print(f"${flight.price:.0f} - {flight.origin} → {flight.destination}")
        print(f"  {flight.departure_time.strftime('%b %d %H:%M')} | {flight.duration_formatted}")
        print(f"  {flight.stops_label} | {', '.join(flight.carriers)}")

    # Round-trip search
    roundtrips = finder.search_roundtrip(
        origin="SFO",
        destination="anywhere",  # Find cheapest destinations
        departure_from=date.today() + timedelta(days=30),
        min_days=7,
        max_days=14,
        max_price=500,
    )

    for rt in roundtrips:
        print(f"${rt.price:.0f} - {rt.origin} ⇄ {rt.destination}")
        print(f"  {rt.trip_days} days | {rt.destination_city}")

    # Location search
    locations = finder.find_location("San Francisco")
    for loc in locations:
        print(f"{loc.id} - {loc.name} ({loc.type})")
```

### Async API

```python
import asyncio
from flightfinder import AsyncFlightFinder
from datetime import date, timedelta

async def search_multiple_origins():
    async with AsyncFlightFinder() as finder:
        # Search from multiple airports concurrently
        results = await finder.search_multiple_origins(
            origins=["SFO", "OAK", "SJC"],
            destination="LAX",
            departure_from=date.today() + timedelta(days=30),
        )

        for origin, flights in results.items():
            print(f"\nFrom {origin}:")
            for flight in flights[:3]:
                print(f"  ${flight.price:.0f} - {flight.duration_formatted}")

asyncio.run(search_multiple_origins())
```

### CLI Usage

```bash
# One-way search
flights search SFO -d LAX --days 30 --max-stops 1

# Round-trip search
flights roundtrip SFO -d anywhere --min-days 7 --max-days 14 --max-price 500

# Search to anywhere
flights search SFO --days 30 --format json -o flights.json

# Location search
flights location "San Francisco" --type AIRPORT

# Export to CSV
flights search SFO -d LAX --format csv -o results.csv

# Interactive mode
flights repl
```

## CLI Commands

### `flights search`
Search for one-way flights.

```bash
flights search <origin> [options]

Options:
  -d, --destination    Destination (default: anywhere)
  --days              Days from now to start search (default: 30)
  --window            Search window in days (default: 7)
  --max-stops         Maximum stops (default: 1)
  --max-price         Maximum price filter
  --min-price         Minimum price filter
  --limit             Number of results (default: 20)
  --sort              Sort by: PRICE, DURATION, QUALITY (default: PRICE)
  --cabin             Cabin class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
  --format            Output format: table, json, csv (default: table)
  -o, --output        Output file path
  -v, --verbose       Enable verbose logging
```

### `flights roundtrip`
Search for round-trip flights.

```bash
flights roundtrip <origin> [options]

Options:
  (same as search, plus:)
  --min-days          Minimum trip duration (default: 7)
  --max-days          Maximum trip duration (default: 14)
  --return-from       Days from now for earliest return
  --return-to         Days from now for latest return
```

### `flights location`
Search for airport/city codes.

```bash
flights location <query> [options]

Options:
  --type              Filter by: AIRPORT, CITY, COUNTRY
  --limit             Maximum results (default: 10)
  --format            Output format: table, json, csv
```

### `flights repl`
Start interactive mode.

```bash
flights repl

# In REPL:
flights> search SFO LAX
flights> roundtrip SFO anywhere
flights> location Tokyo
flights> cache
flights> clear
flights> quit
```

## Configuration

FlightFinder can be configured via file or environment variables.

### Config File

Create `~/.flightfinder/config.json` or `./flightfinder.json`:

```json
{
  "api": {
    "timeout": 30.0,
    "max_retries": 3,
    "retry_delay": 1.0,
    "retry_backoff": 2.0
  },
  "cache": {
    "enabled": true,
    "ttl_seconds": 300,
    "max_size": 100
  },
  "search_defaults": {
    "adults": 1,
    "cabin_class": "ECONOMY",
    "max_stops": 2,
    "sort_by": "PRICE",
    "limit": 100
  }
}
```

### Environment Variables

```bash
export FLIGHTFINDER_API_URL="https://api.skypicker.com/umbrella/v2/graphql"
export FLIGHTFINDER_TIMEOUT=30
export FLIGHTFINDER_MAX_RETRIES=3
export FLIGHTFINDER_CACHE_ENABLED=true
export FLIGHTFINDER_CACHE_TTL=300
export FLIGHTFINDER_CONFIG=/path/to/config.json
```

### Programmatic Configuration

```python
from flightfinder import FlightFinder, Config

config = Config()
config.api.timeout = 60.0
config.cache.enabled = True
config.cache.ttl_seconds = 600

finder = FlightFinder(config=config)
```

## Deal Alerts

Set up price alerts for routes you want to monitor:

```python
from flightfinder.alerts import DealAlertManager, PriceAlert, format_alert_match

manager = DealAlertManager()

# Add an alert
alert = PriceAlert(
    origin="SFO",
    destination="LAX",
    max_price=150,
    round_trip=True,
    min_days=7,
    max_days=14,
    name="LA Weekend Trip",
)
manager.add_alert(alert)

# Set callback for matches
def on_deal(match):
    print(format_alert_match(match))

manager.on_match = on_deal

# Check alerts
matches = manager.check_alerts(days_ahead=30, window=14)
print(f"Found {len(matches)} deals!")

# Alerts are persisted to ~/.flightfinder/alerts.json
manager.close()
```

## Data Models

### Flight
```python
flight.price           # float: Price in USD
flight.origin          # str: Origin airport code
flight.destination     # str: Destination airport code
flight.departure_time  # datetime: Departure time
flight.arrival_time    # datetime: Arrival time
flight.duration_minutes # int: Total flight duration
flight.stops           # int: Number of stops
flight.carriers        # list[str]: Airline names
flight.segments        # list[Segment]: Individual flight segments
flight.deep_link       # str: Booking URL
flight.duration_formatted  # str: "2h 30m"
flight.stops_label     # str: "Direct", "1 stop", "2 stops"
```

### RoundTrip
```python
rt.price              # float: Total round-trip price
rt.outbound           # Flight: Outbound flight
rt.inbound            # Flight: Return flight
rt.trip_days          # int: Days between flights
rt.destination_city   # str: Destination city name
rt.destination_country # str: Country code
rt.checked_bag_price  # float: First checked bag price
rt.price_with_bag     # float: Total with bag
rt.is_domestic        # bool: True if within US
rt.is_international   # bool: True if outside US
```

### Location
```python
loc.id            # str: Location ID / airport code
loc.name          # str: Full name
loc.type          # str: AIRPORT, CITY, COUNTRY
loc.city          # str: City name
loc.country       # str: Country name
loc.country_code  # str: Country code
loc.latitude      # float: GPS latitude
loc.longitude     # float: GPS longitude
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=flightfinder

# Run specific test file
pytest tests/test_client.py -v

# Run specific test
pytest tests/test_models.py::TestFlight::test_duration_formatted -v
```

## Project Structure

```
flightfinder/
├── src/flightfinder/
│   ├── __init__.py      # Package exports
│   ├── client.py        # Sync FlightFinder client
│   ├── async_client.py  # Async FlightFinder client
│   ├── models.py        # Data models (Flight, Location, etc.)
│   ├── queries.py       # GraphQL query definitions
│   ├── config.py        # Configuration management
│   ├── cache.py         # Response caching
│   ├── exceptions.py    # Custom exceptions
│   ├── alerts.py        # Deal alert system
│   └── cli.py           # Command-line interface
├── tests/               # Test suite
├── examples/            # Example scripts
└── pyproject.toml       # Project configuration
```

## API Notes

- No authentication required (public API)
- Content providers: KIWI, FRESH, KAYAK
- Sort options: PRICE, QUALITY, DURATION, POPULARITY
- Cabin classes: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
- For "anywhere" searches, pass the literal string `"anywhere"` as destination

## License

MIT License
