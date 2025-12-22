"""Data models for flight search results."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Location(BaseModel):
    """Airport, city, or country location."""

    id: str
    name: str
    slug: str
    type: str  # AIRPORT, CITY, COUNTRY, etc.
    city: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def __str__(self) -> str:
        if self.type == "AIRPORT":
            return f"{self.name} ({self.id}) - {self.city}, {self.country}"
        return f"{self.name} ({self.type})"


class Segment(BaseModel):
    """A single flight segment within an itinerary."""

    carrier: str
    carrier_name: Optional[str] = None
    flight_number: Optional[str] = None
    departure_time: datetime
    arrival_time: datetime
    origin: str
    origin_name: Optional[str] = None
    destination: str
    destination_name: Optional[str] = None
    duration_minutes: int
    cabin_class: Optional[str] = None


class Flight(BaseModel):
    """A complete flight option (may have multiple segments/stops)."""

    id: str
    price: float
    currency: str = "USD"
    departure_time: datetime
    arrival_time: datetime
    origin: str
    origin_city: Optional[str] = None
    destination: str
    destination_city: Optional[str] = None
    duration_minutes: int
    stops: int = 0
    segments: list[Segment] = Field(default_factory=list)
    deep_link: Optional[str] = None

    @property
    def duration_formatted(self) -> str:
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        return f"{hours}h {minutes}m"

    @property
    def stops_label(self) -> str:
        if self.stops == 0:
            return "Direct"
        elif self.stops == 1:
            return "1 stop"
        return f"{self.stops} stops"

    def __str__(self) -> str:
        return (
            f"${self.price:.0f} | {self.origin} → {self.destination} | "
            f"{self.departure_time.strftime('%b %d %H:%M')} | "
            f"{self.duration_formatted} | {self.stops_label}"
        )


class Itinerary(BaseModel):
    """A complete travel itinerary (outbound + optional return)."""

    id: str
    price: float
    currency: str = "USD"
    outbound: Flight
    inbound: Optional[Flight] = None
    booking_url: Optional[str] = None

    @property
    def is_round_trip(self) -> bool:
        return self.inbound is not None

    def __str__(self) -> str:
        trip_type = "Round trip" if self.is_round_trip else "One way"
        return f"${self.price:.0f} {trip_type}: {self.outbound}"
