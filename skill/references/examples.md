# FlightFinder Examples

## Common Use Cases

### Finding Cheap Flights to Anywhere

```bash
# From San Francisco, departing in 30 days
./scripts/search.sh SFO anywhere 30
```

### Planning a Week in Tokyo

```bash
# Round-trip from LAX, 7-10 day trip, departing in 45 days
./scripts/roundtrip.sh LAX tokyo 45 7 10

# Hotels in Tokyo
./scripts/hotels.sh tokyo
```

### Budget Trip Planning

```bash
# Combined search with estimated total
./scripts/trip.sh SFO "new york" 30 5
```

### Finding Airport Codes

```bash
# Look up airports near a city
./scripts/location.sh "Los Angeles"
./scripts/location.sh "London"
./scripts/location.sh "Sydney"
```

## Example JSON Outputs

### One-Way Flight Search

```json
{
  "count": 5,
  "search": {
    "origin": "SFO",
    "destination": "LAX",
    "dates": "2026-02-23 to 2026-03-02"
  },
  "flights": [
    {
      "price": 89.0,
      "origin": "SFO",
      "destination": "LAX",
      "departure": "2026-02-24T06:00:00",
      "arrival": "2026-02-24T07:25:00",
      "duration": "1h 25m",
      "stops": 0,
      "carriers": ["United"],
      "booking_url": "https://www.kiwi.com/..."
    }
  ]
}
```

### Round-Trip Search

```json
{
  "count": 10,
  "search": {
    "origin": "SFO",
    "destination": "NRT",
    "depart_around": "2026-02-23",
    "trip_duration": "7-14 days"
  },
  "roundtrips": [
    {
      "price": 892.0,
      "price_with_bag": 942.0,
      "origin": "SFO",
      "destination": "NRT",
      "destination_city": "Tokyo",
      "outbound_date": "2026-02-25",
      "return_date": "2026-03-04",
      "trip_days": 7,
      "outbound_stops": 0,
      "return_stops": 1,
      "carriers": ["ANA", "United"],
      "booking_url": "https://www.kiwi.com/..."
    }
  ]
}
```

### Hotel Search

```json
{
  "count": 20,
  "total_available": 150,
  "location": "tokyo",
  "hotels": [
    {
      "name": "Park Hyatt Tokyo",
      "type": "Hotel",
      "price_range": "$400-600",
      "min_price": 400,
      "max_price": 600,
      "rating": 4.8,
      "review_count": 2500,
      "url": "https://www.tripadvisor.com/...",
      "highlights": ["Luxury", "City views", "Spa"]
    }
  ]
}
```

### Combined Trip Search

```json
{
  "origin": "SFO",
  "destination": "tokyo",
  "dates": {
    "depart_around": "2026-02-23",
    "nights": 7
  },
  "flights": [
    {
      "price": 892.0,
      "dates": "2026-02-25 - 2026-03-04",
      "trip_days": 7,
      "carriers": ["ANA", "United"]
    }
  ],
  "hotels": [
    {
      "name": "Shinjuku Granbell Hotel",
      "price_per_night": 120.0,
      "rating": 4.3,
      "type": "Hotel"
    }
  ],
  "estimated_total": {
    "flight": 892.0,
    "hotel_per_night": 120.0,
    "hotel_total": 840.0,
    "total": 1732.0,
    "nights": 7
  }
}
```

### Location Lookup

```json
{
  "count": 3,
  "query": "San Francisco",
  "locations": [
    {
      "code": "SFO",
      "name": "San Francisco International Airport",
      "type": "AIRPORT",
      "city": "San Francisco",
      "country": "United States",
      "country_code": "US"
    },
    {
      "code": "OAK",
      "name": "Oakland International Airport",
      "type": "AIRPORT",
      "city": "Oakland",
      "country": "United States",
      "country_code": "US"
    }
  ]
}
```

## Supported Hotel Locations

Major cities with hotel search support:
- **US**: New York, Los Angeles, San Francisco, Las Vegas, Miami, Chicago, Seattle
- **Europe**: London, Paris, Rome, Barcelona, Amsterdam
- **Asia**: Tokyo, Osaka, Seoul, Bangkok, Singapore, Hong Kong
- **Other**: Sydney, Dubai, Cancun

Use city name directly in hotel searches. For unsupported cities, use the TripAdvisor location key (e.g., "g60763" for New York).
