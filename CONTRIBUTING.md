# Contributing to FlightFinder

Thank you for your interest in contributing to FlightFinder! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/flightfinder.git
   cd flightfinder
   ```

2. **Install dependencies:**

   Using uv (recommended):
   ```bash
   uv sync
   ```

   Using pip:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Verify installation:**
   ```bash
   flights --help
   pytest
   ```

## Code Style

### Formatting and Linting

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/
```

### Type Hints

Type hints are required for all function signatures:

```python
def search_flights(
    origin: str,
    destination: str,
    departure_from: date,
    max_stops: int = 1,
) -> list[Flight]:
    ...
```

### Documentation

- Add docstrings to public functions and classes
- Use Google-style docstrings
- Keep comments concise and meaningful

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=flightfinder --cov-report=term-missing

# Run specific test file
pytest tests/test_client.py -v

# Run specific test
pytest tests/test_models.py::TestFlight::test_duration -v

# Skip integration tests (require network)
pytest -m "not integration"
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_<module>.py`
- Use descriptive test function names
- Aim for >80% code coverage

Example test:

```python
def test_search_flights_returns_results():
    """Test that search_flights returns a list of Flight objects."""
    with FlightFinder() as finder:
        flights = finder.search_flights(
            origin="SFO",
            destination="LAX",
            departure_from=date.today() + timedelta(days=30),
            limit=5,
        )
        assert isinstance(flights, list)
        assert all(isinstance(f, Flight) for f in flights)
```

## Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clean, well-documented code
   - Add tests for new functionality
   - Update documentation if needed

3. **Run quality checks:**
   ```bash
   ruff check src/ tests/
   pytest --cov=flightfinder
   ```

4. **Commit your changes:**
   - Use clear, descriptive commit messages
   - Follow [Conventional Commits](https://www.conventionalcommits.org/) format:
     - `feat:` for new features
     - `fix:` for bug fixes
     - `docs:` for documentation changes
     - `refactor:` for code refactoring
     - `test:` for adding tests

5. **Push and create a PR:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **PR Requirements:**
   - All tests pass
   - Lint checks pass
   - Coverage does not decrease
   - Code is reviewed and approved

## Project Structure

```
flightfinder/
├── src/flightfinder/
│   ├── __init__.py       # Package exports
│   ├── client.py         # Sync FlightFinder client
│   ├── async_client.py   # Async client
│   ├── models.py         # Flight data models
│   ├── hotel_client.py   # HotelFinder client
│   ├── hotel_models.py   # Hotel data models
│   ├── queries.py        # GraphQL queries
│   ├── config.py         # Configuration
│   ├── cache.py          # Response caching
│   ├── alerts.py         # Deal alerts
│   ├── discord.py        # Discord integration
│   ├── mcp_server.py     # MCP server
│   ├── exceptions.py     # Custom exceptions
│   └── cli.py            # CLI interface
├── tests/                # Test suite
├── examples/             # Example scripts
└── pyproject.toml        # Project config
```

## Reporting Issues

When reporting bugs, please include:

1. Python version (`python --version`)
2. FlightFinder version (`flights --version`)
3. Operating system
4. Steps to reproduce
5. Expected vs actual behavior
6. Error messages or stack traces

## Questions?

Feel free to open an issue for any questions or concerns. We're happy to help!
