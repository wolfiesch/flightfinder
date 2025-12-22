"""Deal alert system for FlightFinder."""

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

from flightfinder.client import FlightFinder
from flightfinder.models import Flight, RoundTrip

logger = logging.getLogger(__name__)


@dataclass
class PriceAlert:
    """A price alert configuration."""

    origin: str
    destination: str = "anywhere"
    max_price: float = 500.0
    min_days: int = 7
    max_days: int = 14
    max_stops: int = 1
    departure_from: Optional[date] = None
    departure_to: Optional[date] = None
    round_trip: bool = True
    cabin_class: str = "ECONOMY"
    name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "origin": self.origin,
            "destination": self.destination,
            "max_price": self.max_price,
            "min_days": self.min_days,
            "max_days": self.max_days,
            "max_stops": self.max_stops,
            "departure_from": self.departure_from.isoformat() if self.departure_from else None,
            "departure_to": self.departure_to.isoformat() if self.departure_to else None,
            "round_trip": self.round_trip,
            "cabin_class": self.cabin_class,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PriceAlert":
        """Create from dictionary."""
        departure_from = None
        if data.get("departure_from"):
            departure_from = date.fromisoformat(data["departure_from"])

        departure_to = None
        if data.get("departure_to"):
            departure_to = date.fromisoformat(data["departure_to"])

        created_at = datetime.now()
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        return cls(
            origin=data["origin"],
            destination=data.get("destination", "anywhere"),
            max_price=data.get("max_price", 500.0),
            min_days=data.get("min_days", 7),
            max_days=data.get("max_days", 14),
            max_stops=data.get("max_stops", 1),
            departure_from=departure_from,
            departure_to=departure_to,
            round_trip=data.get("round_trip", True),
            cabin_class=data.get("cabin_class", "ECONOMY"),
            name=data.get("name"),
            created_at=created_at,
        )


@dataclass
class AlertMatch:
    """A flight that matches an alert."""

    alert: PriceAlert
    flight: Flight | RoundTrip
    price_delta: float  # How much below max_price


AlertCallback = Callable[[AlertMatch], None]


class DealAlertManager:
    """
    Manages price alerts and checks for matching deals.

    Usage:
        manager = DealAlertManager()

        # Add an alert
        alert = PriceAlert(origin="SFO", destination="LAX", max_price=150)
        manager.add_alert(alert)

        # Set callback for matches
        def on_deal(match: AlertMatch):
            print(f"Deal found! ${match.flight.price}")

        manager.on_match = on_deal

        # Check alerts
        matches = manager.check_alerts()
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the alert manager.

        Args:
            storage_path: Path to persist alerts. Defaults to ~/.flightfinder/alerts.json
        """
        self.storage_path = storage_path or Path.home() / ".flightfinder" / "alerts.json"
        self.alerts: list[PriceAlert] = []
        self.on_match: Optional[AlertCallback] = None
        self._finder: Optional[FlightFinder] = None

        self._load_alerts()

    @property
    def finder(self) -> FlightFinder:
        """Get or create the FlightFinder client."""
        if self._finder is None:
            self._finder = FlightFinder()
        return self._finder

    def add_alert(self, alert: PriceAlert) -> None:
        """Add a new price alert."""
        self.alerts.append(alert)
        self._save_alerts()
        logger.info(f"Added alert: {alert.origin} → {alert.destination} ≤${alert.max_price}")

    def remove_alert(self, index: int) -> Optional[PriceAlert]:
        """Remove an alert by index."""
        if 0 <= index < len(self.alerts):
            alert = self.alerts.pop(index)
            self._save_alerts()
            logger.info(f"Removed alert: {alert.origin} → {alert.destination}")
            return alert
        return None

    def clear_alerts(self) -> int:
        """Remove all alerts. Returns number cleared."""
        count = len(self.alerts)
        self.alerts.clear()
        self._save_alerts()
        return count

    def check_alerts(
        self,
        days_ahead: int = 30,
        window: int = 14,
    ) -> list[AlertMatch]:
        """
        Check all alerts for matching deals.

        Args:
            days_ahead: Days from now to start searching
            window: Search window in days

        Returns:
            List of matching deals
        """
        matches: list[AlertMatch] = []

        for alert in self.alerts:
            try:
                alert_matches = self._check_alert(alert, days_ahead, window)
                matches.extend(alert_matches)

                # Fire callback for each match
                if self.on_match:
                    for match in alert_matches:
                        self.on_match(match)

            except Exception as e:
                logger.error(f"Error checking alert {alert.name or alert.origin}: {e}")

        return matches

    def _check_alert(
        self,
        alert: PriceAlert,
        days_ahead: int,
        window: int,
    ) -> list[AlertMatch]:
        """Check a single alert for matches."""
        departure_from = alert.departure_from or (date.today() + timedelta(days=days_ahead))
        departure_to = alert.departure_to or (departure_from + timedelta(days=window))

        matches: list[AlertMatch] = []

        if alert.round_trip:
            roundtrips = self.finder.search_roundtrip(
                origin=alert.origin,
                destination=alert.destination,
                departure_from=departure_from,
                departure_to=departure_to,
                min_days=alert.min_days,
                max_days=alert.max_days,
                max_stops=alert.max_stops,
                max_price=alert.max_price,
                cabin_class=alert.cabin_class,
                limit=20,
            )

            for rt in roundtrips:
                if rt.price <= alert.max_price:
                    matches.append(
                        AlertMatch(
                            alert=alert,
                            flight=rt,
                            price_delta=alert.max_price - rt.price,
                        )
                    )
        else:
            flights = self.finder.search_flights(
                origin=alert.origin,
                destination=alert.destination,
                departure_from=departure_from,
                departure_to=departure_to,
                max_stops=alert.max_stops,
                max_price=alert.max_price,
                cabin_class=alert.cabin_class,
                limit=20,
            )

            for flight in flights:
                if flight.price <= alert.max_price:
                    matches.append(
                        AlertMatch(
                            alert=alert,
                            flight=flight,
                            price_delta=alert.max_price - flight.price,
                        )
                    )

        logger.info(f"Alert {alert.origin}→{alert.destination}: {len(matches)} matches")
        return matches

    def _load_alerts(self) -> None:
        """Load alerts from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path) as f:
                    data = json.load(f)
                    self.alerts = [PriceAlert.from_dict(a) for a in data]
                logger.debug(f"Loaded {len(self.alerts)} alerts from {self.storage_path}")
            except Exception as e:
                logger.warning(f"Failed to load alerts: {e}")
                self.alerts = []
        else:
            self.alerts = []

    def _save_alerts(self) -> None:
        """Save alerts to storage."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump([a.to_dict() for a in self.alerts], f, indent=2)
            logger.debug(f"Saved {len(self.alerts)} alerts to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save alerts: {e}")

    def close(self) -> None:
        """Close the FlightFinder client."""
        if self._finder:
            self._finder.close()
            self._finder = None


def format_alert_match(match: AlertMatch) -> str:
    """Format an alert match for display."""
    flight = match.flight

    if isinstance(flight, RoundTrip):
        out_date = flight.outbound.departure_time.strftime("%b %d")
        in_date = flight.inbound.departure_time.strftime("%b %d")
        return (
            f"${flight.price:.0f} ({match.alert.origin}→{flight.destination}) | "
            f"{out_date} - {in_date} ({flight.trip_days} days) | "
            f"${match.price_delta:.0f} below target"
        )
    else:
        dep_date = flight.departure_time.strftime("%b %d")
        return (
            f"${flight.price:.0f} ({match.alert.origin}→{flight.destination}) | "
            f"{dep_date} | {flight.duration_formatted} | "
            f"${match.price_delta:.0f} below target"
        )
