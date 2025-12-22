"""FlightFinder - Python client for Kiwi/Skypicker flight search API."""

from flightfinder.client import FlightFinder
from flightfinder.models import Flight, Location, Itinerary

__all__ = ["FlightFinder", "Flight", "Location", "Itinerary"]
__version__ = "0.1.0"
