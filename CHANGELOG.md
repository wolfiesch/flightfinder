# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-24

### Added

- **Flight Search**
  - One-way and round-trip flight search via Kiwi/Skypicker GraphQL API
  - "Anywhere" destination search for finding cheapest destinations
  - Location/airport code lookup
  - Async client (`AsyncFlightFinder`) for concurrent searches
  - Response caching with configurable TTL
  - Retry logic with exponential backoff
  - Rate limit handling

- **Hotel Search**
  - Hotel search via Xotelo API (`HotelFinder` class)
  - Support for 30+ major cities worldwide
  - Price range and rating filters
  - Accommodation type filtering (Hotel, Hostel, Resort, etc.)

- **Combined Trip Planning**
  - `flights trip` command for searching flights and hotels together
  - Estimated trip cost calculation

- **MCP Server**
  - Model Context Protocol server for AI agent integration
  - Tools: `search_flights`, `search_roundtrip`, `find_location`, `search_hotels`, `search_trip`
  - Stdio transport for local use
  - Ready for Claude Code integration

- **Discord Integration**
  - Webhook notifications for search results
  - `--discord` flag on CLI commands
  - Rich embed formatting for flights and hotels

- **Background Monitoring**
  - Fly.io deployment support for continuous monitoring
  - Configurable search intervals

- **CLI Features**
  - Multiple output formats: table, JSON, CSV
  - Interactive REPL mode
  - Export to file with `-o` flag

- **Deal Alerts**
  - Price alert system for monitoring routes
  - Persistent alert storage

### Changed

- Upgraded to Python 3.10+ minimum requirement
- Version bumped from 0.3.0 to 1.0.0 for stable release

### Documentation

- Added comprehensive README with all features
- Added CONTRIBUTING.md with development guidelines
- Added LICENSE (MIT)
- Added mcp.json for Claude Code integration

## [0.3.0] - 2025-12-XX

### Added

- Hotel search functionality via Xotelo API
- Discord webhook integration
- Background monitoring service
- Combined trip search command

## [0.2.0] - 2025-11-XX

### Added

- Async client for concurrent searches
- Response caching
- Deal alert system
- Multiple output formats (JSON, CSV)
- REPL mode

## [0.1.0] - 2025-10-XX

### Added

- Initial release
- Basic flight search functionality
- Location search
- CLI interface with rich output
