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
    def duration_short(self) -> str:
        """Compact duration format: '4h' or '4h30'."""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if minutes == 0:
            return f"{hours}h"
        return f"{hours}h{minutes:02d}"

    @property
    def departure_time_short(self) -> str:
        """Departure time as compact '6a' or '11p' format."""
        hour = self.departure_time.hour
        minute = self.departure_time.minute
        am_pm = "a" if hour < 12 else "p"
        display_hour = hour if 1 <= hour <= 12 else (hour - 12 if hour > 12 else 12)
        if minute == 0:
            return f"{display_hour}{am_pm}"
        return f"{display_hour}:{minute:02d}{am_pm}"

    @property
    def carriers(self) -> list[str]:
        """List of unique carrier names for this flight."""
        seen = set()
        result = []
        for seg in self.segments:
            name = seg.carrier_name or seg.carrier
            if name and name not in seen:
                seen.add(name)
                result.append(name)
        return result

    @property
    def layover_airports(self) -> list[str]:
        """List of layover airport codes (connections between segments)."""
        if len(self.segments) <= 1:
            return []
        return [seg.destination for seg in self.segments[:-1]]

    @property
    def layover_duration_minutes(self) -> int:
        """Total layover time in minutes across all connections."""
        if len(self.segments) <= 1:
            return 0
        total = 0
        for i in range(len(self.segments) - 1):
            arrival = self.segments[i].arrival_time
            departure = self.segments[i + 1].departure_time
            layover = (departure - arrival).total_seconds() / 60
            total += int(layover)
        return total

    @property
    def layover_duration_formatted(self) -> str:
        """Layover duration as 'Xh' or 'XhYm' format."""
        mins = self.layover_duration_minutes
        if mins == 0:
            return ""
        hours = mins // 60
        minutes = mins % 60
        if minutes == 0:
            return f"{hours}h"
        return f"{hours}h{minutes:02d}"

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


class RoundTrip(BaseModel):
    """A round-trip flight itinerary with outbound and return flights."""

    id: str
    price: float
    currency: str = "USD"
    outbound: Flight
    inbound: Flight
    booking_url: Optional[str] = None
    checked_bag_price: Optional[float] = None
    destination_country: Optional[str] = None  # Country code (e.g., "US", "CA", "MX")
    destination_city: Optional[str] = None

    @property
    def price_with_bag(self) -> float:
        """Total price including one checked bag."""
        if self.checked_bag_price:
            return self.price + self.checked_bag_price
        return self.price

    @property
    def trip_days(self) -> int:
        """Number of days between outbound departure and inbound departure."""
        delta = self.inbound.departure_time.date() - self.outbound.departure_time.date()
        return delta.days

    @property
    def destination(self) -> str:
        """Primary destination (outbound arrival)."""
        return self.outbound.destination

    @property
    def origin(self) -> str:
        """Origin airport."""
        return self.outbound.origin

    @property
    def is_international(self) -> bool:
        """True if destination is outside the US."""
        return self.destination_country is not None and self.destination_country != "US"

    @property
    def is_domestic(self) -> bool:
        """True if destination is within the US."""
        return self.destination_country == "US"

    @property
    def all_carriers(self) -> list[str]:
        """All unique carrier names across both legs."""
        seen = set()
        result = []
        for carrier in self.outbound.carriers + self.inbound.carriers:
            if carrier not in seen:
                seen.add(carrier)
                result.append(carrier)
        return result

    @property
    def price_per_day(self) -> float:
        """Price divided by trip duration."""
        return self.price / self.trip_days if self.trip_days > 0 else self.price

    @property
    def total_travel_minutes(self) -> int:
        """Combined flight duration of outbound and inbound legs."""
        return self.outbound.duration_minutes + self.inbound.duration_minutes

    @property
    def total_travel_formatted(self) -> str:
        """Total travel time as 'Xh' or 'XhYm' format."""
        mins = self.total_travel_minutes
        hours = mins // 60
        minutes = mins % 60
        if minutes == 0:
            return f"{hours}h"
        return f"{hours}h{minutes:02d}"

    @property
    def all_layover_airports(self) -> list[str]:
        """All unique layover airports from both legs."""
        seen = set()
        result = []
        for airport in self.outbound.layover_airports + self.inbound.layover_airports:
            if airport not in seen:
                seen.add(airport)
                result.append(airport)
        return result

    def __str__(self) -> str:
        out_date = self.outbound.departure_time.strftime("%b %d")
        in_date = self.inbound.departure_time.strftime("%b %d")
        bag_str = f" (+${self.checked_bag_price:.0f} bag)" if self.checked_bag_price else ""
        return (
            f"${self.price:.0f}{bag_str} | {self.origin} → {self.destination} | "
            f"{out_date} - {in_date} ({self.trip_days} days)"
        )
