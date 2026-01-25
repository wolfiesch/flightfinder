# FlightFinder Skill

Search for flights and hotels to plan trips. No API keys required.

## Activation Triggers

Use this skill when the user mentions:
- "find flights", "search flights", "flight to", "fly to"
- "find hotels", "search hotels", "hotels in"
- "plan trip", "trip to", "travel to"
- "cheap flights", "cheapest flights"
- "round trip", "roundtrip"
- "airport code", "what airport"

## Installation

```bash
pip install flightfinder
```

Verify installation:
```bash
flights --help
```

## Available Commands

### One-Way Flight Search

```bash
./scripts/search.sh <origin> <destination> [days_from_now]
```

Example:
```bash
./scripts/search.sh SFO LAX 30
```

Returns JSON with flights sorted by price.

### Round-Trip Search

```bash
./scripts/roundtrip.sh <origin> <destination> <days_from_now> <min_days> <max_days>
```

Example:
```bash
./scripts/roundtrip.sh SFO tokyo 30 7 14
```

### Hotel Search

```bash
./scripts/hotels.sh <city>
```

Example:
```bash
./scripts/hotels.sh "new york"
```

Supported cities: New York, Los Angeles, San Francisco, Tokyo, Paris, London, etc.

### Combined Trip Search

```bash
./scripts/trip.sh <origin> <destination> <days_from_now> <nights>
```

Example:
```bash
./scripts/trip.sh SFO tokyo 30 7
```

Returns both flights and hotels with estimated total cost.

### Airport Lookup

```bash
./scripts/location.sh <query>
```

Example:
```bash
./scripts/location.sh "San Francisco"
```

## Response Format

All scripts output JSON to stdout. Status messages go to stderr.

Example flight response:
```json
{
  "count": 10,
  "search": {
    "origin": "SFO",
    "destination": "LAX",
    "dates": "2026-02-23 to 2026-03-02"
  },
  "flights": [
    {
      "price": 89,
      "origin": "SFO",
      "destination": "LAX",
      "departure": "2026-02-24T06:00:00",
      "duration": "1h 25m",
      "stops": 0,
      "carriers": ["United"],
      "booking_url": "https://..."
    }
  ]
}
```

## Tips

- Use "anywhere" as destination to find cheapest destinations
- Price is in USD
- Stops = 0 means direct flight
- booking_url provides direct link to book

## Error Handling

If `flights` CLI is not installed, scripts will error with instructions.
Network errors return JSON with `"error"` field.
