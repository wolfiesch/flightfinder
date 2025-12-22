# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FlightFinder is a Python client for the Kiwi/Skypicker GraphQL flight search API. It provides programmatic access to flight searches without requiring an API key.

## Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run CLI
flights SFO --days 30 --max-stops 1
flights SFO -d LAX --max-price 200

# Run tests
pytest
pytest tests/test_client.py -v
pytest -k "test_search"

# Run example script
python examples/search_from_sfo.py
```

## Architecture

**API Layer** (`client.py`):
- `FlightFinder` class wraps the Skypicker GraphQL API at `api.skypicker.com/umbrella/v2/graphql`
- Uses httpx for HTTP requests with context manager support
- Two main operations: `find_location()` for airport/city search, `search_flights()` for flight queries
- For "anywhere" searches, pass the literal string `"anywhere"` as destination ID (not a special object)
- Flight searches require `?featureName=SearchOneWayItinerariesQuery` URL parameter

**Data Models** (`models.py`):
- Pydantic models: `Location`, `Segment`, `Flight`, `Itinerary`
- `Flight` contains list of `Segment` objects for multi-leg flights
- API returns price amounts as strings; parsing handles this

**CLI** (`cli.py`):
- Entry point registered as `flights` command
- Uses rich for formatted table output

## API Notes

- No authentication required (public API)
- Content providers: KIWI, FRESH, KAYAK
- Sort options: PRICE, QUALITY, DURATION, POPULARITY
- Cabin classes: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
- GraphQL queries use union types with `__typename` for error handling (`AppError` vs success types)
