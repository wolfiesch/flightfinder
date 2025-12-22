"""FlightFinder - Python client for Kiwi/Skypicker flight search API."""

from flightfinder.client import FlightFinder
from flightfinder.models import Flight, Location, Itinerary, RoundTrip, Segment

__all__ = ["FlightFinder", "Flight", "Location", "Itinerary", "RoundTrip", "Segment"]
__version__ = "0.1.0"
