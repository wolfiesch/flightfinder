"""Discord webhook integration for FlightFinder notifications."""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import httpx

from flightfinder.models import Flight, RoundTrip, Segment
from flightfinder.alerts import AlertMatch, PriceAlert
from flightfinder.hotel_models import Hotel, HotelSearchResults

logger = logging.getLogger(__name__)

# Discord embed colors
COLOR_DEAL_ALERT = 0xFF0000  # Red - urgent deals
COLOR_FLIGHT = 0x00FF00  # Green - good price
COLOR_ROUNDTRIP = 0x00AA00  # Dark green
COLOR_SEGMENT = 0x3498DB  # Blue - segment details
COLOR_LAYOVER = 0xF39C12  # Orange - layover info
COLOR_SEARCH_HEADER = 0x9B59B6  # Purple - search header
COLOR_STATUS = 0x7289DA  # Discord blurple - status
COLOR_HOTEL = 0x1ABC9C  # Teal - hotel
COLOR_HOTEL_EXCELLENT = 0x2ECC71  # Emerald - 4.5+ rating
COLOR_HOTEL_GOOD = 0x3498DB  # Blue - 4.0+ rating
COLOR_TRIP = 0xE91E63  # Pink - combined trip


@dataclass
class DiscordConfig:
    """Discord notification configuration."""

    webhook_url: str = ""
    enabled: bool = True
    verbose_level: str = "ultra"  # minimal, normal, verbose, ultra
    send_search_results: bool = True
    send_deal_alerts: bool = True
    send_monitoring_status: bool = True
    rate_limit_delay: float = 0.5  # Delay between messages in seconds
    embed_color_deal: int = COLOR_DEAL_ALERT
    embed_color_flight: int = COLOR_FLIGHT
    embed_color_segment: int = COLOR_SEGMENT

    @classmethod
    def from_dict(cls, data: dict) -> "DiscordConfig":
        """Create config from dictionary."""
        return cls(
            webhook_url=data.get("webhook_url", ""),
            enabled=data.get("enabled", True),
            verbose_level=data.get("verbose_level", "ultra"),
            send_search_results=data.get("send_search_results", True),
            send_deal_alerts=data.get("send_deal_alerts", True),
            send_monitoring_status=data.get("send_monitoring_status", True),
            rate_limit_delay=data.get("rate_limit_delay", 0.5),
            embed_color_deal=int(data.get("embed_color_deal", COLOR_DEAL_ALERT)),
            embed_color_flight=int(data.get("embed_color_flight", COLOR_FLIGHT)),
            embed_color_segment=int(data.get("embed_color_segment", COLOR_SEGMENT)),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "webhook_url": self.webhook_url,
            "enabled": self.enabled,
            "verbose_level": self.verbose_level,
            "send_search_results": self.send_search_results,
            "send_deal_alerts": self.send_deal_alerts,
            "send_monitoring_status": self.send_monitoring_status,
            "rate_limit_delay": self.rate_limit_delay,
            "embed_color_deal": self.embed_color_deal,
            "embed_color_flight": self.embed_color_flight,
            "embed_color_segment": self.embed_color_segment,
        }


class DiscordNotifier:
    """
    Discord webhook notifier for flight deals.

    Sends ultra-verbose flight information to a Discord channel.

    Usage:
        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/...")

        # Send a single flight
        notifier.send_flight(flight)

        # Send a round-trip
        notifier.send_roundtrip(roundtrip)

        # Send deal alert
        notifier.send_deal_alert(match)

        # Send all search results
        notifier.send_search_results(origin, destination, flights)
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        config: Optional[DiscordConfig] = None,
    ):
        """
        Initialize the Discord notifier.

        Args:
            webhook_url: Discord webhook URL. If not provided, uses config or env var.
            config: Full Discord configuration. Overrides webhook_url if provided.
        """
        self.config = config or DiscordConfig()

        # Priority: explicit webhook_url > config > env var
        if webhook_url:
            self.config.webhook_url = webhook_url
        elif not self.config.webhook_url:
            self.config.webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")

        self._client = httpx.Client(timeout=30.0)
        self._last_send_time = 0.0

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "DiscordNotifier":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    # =========================================================================
    # Public API - High-level send methods
    # =========================================================================

    def send_flight(self, flight: Flight, search_context: Optional[str] = None) -> bool:
        """
        Send a single flight to Discord with full details.

        Sends multiple embeds:
        1. Flight overview
        2. One embed per segment
        3. Layover info (if connections exist)
        """
        if not self._can_send():
            return False

        embeds = []

        # Main flight overview
        embeds.append(self._build_flight_embed(flight, search_context))

        # Individual segments (ultra verbose mode)
        if self.config.verbose_level in ("verbose", "ultra"):
            for i, segment in enumerate(flight.segments):
                embeds.append(self._build_segment_embed(segment, i + 1, len(flight.segments)))

        # Layover info
        if flight.stops > 0 and self.config.verbose_level == "ultra":
            layover_embeds = self._build_layover_embeds(flight)
            embeds.extend(layover_embeds)

        return self._send_embeds(embeds)

    def send_roundtrip(
        self,
        roundtrip: RoundTrip,
        search_context: Optional[str] = None,
    ) -> bool:
        """
        Send a round-trip itinerary to Discord with exhaustive details.

        Sends multiple embeds:
        1. Trip summary
        2. Outbound flight overview
        3. Outbound segments
        4. Inbound flight overview
        5. Inbound segments
        6. Value analysis
        """
        if not self._can_send():
            return False

        embeds = []

        # Trip summary
        embeds.append(self._build_roundtrip_summary_embed(roundtrip, search_context))

        # Outbound details
        embeds.append(self._build_flight_embed(
            roundtrip.outbound,
            context=f"OUTBOUND: {roundtrip.origin} → {roundtrip.destination}",
        ))

        if self.config.verbose_level in ("verbose", "ultra"):
            for i, segment in enumerate(roundtrip.outbound.segments):
                embeds.append(self._build_segment_embed(
                    segment, i + 1, len(roundtrip.outbound.segments), "Outbound"
                ))

        # Inbound details
        embeds.append(self._build_flight_embed(
            roundtrip.inbound,
            context=f"RETURN: {roundtrip.destination} → {roundtrip.origin}",
        ))

        if self.config.verbose_level in ("verbose", "ultra"):
            for i, segment in enumerate(roundtrip.inbound.segments):
                embeds.append(self._build_segment_embed(
                    segment, i + 1, len(roundtrip.inbound.segments), "Return"
                ))

        # Value analysis (ultra mode)
        if self.config.verbose_level == "ultra":
            embeds.append(self._build_value_analysis_embed(roundtrip))

        return self._send_embeds(embeds)

    def send_deal_alert(self, match: AlertMatch) -> bool:
        """
        Send a deal alert notification to Discord.

        Includes special formatting to highlight the deal.
        """
        if not self._can_send():
            return False

        embeds = [self._build_deal_alert_embed(match)]

        # Include full flight details
        if isinstance(match.flight, RoundTrip):
            embeds.append(self._build_roundtrip_summary_embed(match.flight))
            if self.config.verbose_level in ("verbose", "ultra"):
                embeds.append(self._build_value_analysis_embed(match.flight))
        else:
            embeds.append(self._build_flight_embed(match.flight))

        return self._send_embeds(embeds)

    def send_search_results(
        self,
        origin: str,
        destination: str,
        flights: list[Flight] | list[RoundTrip],
        search_params: Optional[dict] = None,
    ) -> int:
        """
        Send all search results to Discord.

        Returns the number of flights successfully sent.
        """
        if not self._can_send():
            return 0

        # Send search header
        self._send_embeds([self._build_search_header_embed(
            origin, destination, len(flights), search_params
        )])

        sent_count = 0

        for flight in flights:
            try:
                if isinstance(flight, RoundTrip):
                    if self.send_roundtrip(flight, f"Search: {origin} → {destination}"):
                        sent_count += 1
                else:
                    if self.send_flight(flight, f"Search: {origin} → {destination}"):
                        sent_count += 1
            except Exception as e:
                logger.error(f"Error sending flight to Discord: {e}")

        # Send summary
        self._send_embeds([self._build_search_summary_embed(origin, destination, sent_count)])

        return sent_count

    def send_monitoring_status(
        self,
        alerts: list[PriceAlert],
        last_check: Optional[datetime] = None,
        next_check: Optional[datetime] = None,
        matches_found: int = 0,
    ) -> bool:
        """Send a monitoring status update to Discord."""
        if not self._can_send():
            return False

        embed = self._build_monitoring_status_embed(alerts, last_check, next_check, matches_found)
        return self._send_embeds([embed])

    def send_heartbeat(self, message: str = "FlightFinder monitor is alive") -> bool:
        """Send a simple heartbeat message."""
        if not self._can_send():
            return False

        embed = {
            "title": "💓 Heartbeat",
            "description": message,
            "color": COLOR_STATUS,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return self._send_embeds([embed])

    # =========================================================================
    # Hotel Methods
    # =========================================================================

    def send_hotel(self, hotel: Hotel, search_context: Optional[str] = None) -> bool:
        """
        Send a single hotel to Discord with full details.

        Args:
            hotel: Hotel object to send
            search_context: Optional context string (e.g., "Hotels in Tokyo")
        """
        if not self._can_send():
            return False

        embeds = [self._build_hotel_embed(hotel, search_context)]
        return self._send_embeds(embeds)

    def send_hotel_results(
        self,
        location: str,
        hotels: list[Hotel],
        search_params: Optional[dict] = None,
    ) -> int:
        """
        Send hotel search results to Discord.

        Args:
            location: Location searched (city name or key)
            hotels: List of hotels to send
            search_params: Optional search parameters for the header

        Returns:
            Number of hotels successfully sent
        """
        if not self._can_send():
            return 0

        # Send search header
        self._send_embeds([self._build_hotel_search_header_embed(
            location, len(hotels), search_params
        )])

        sent_count = 0

        for hotel in hotels:
            try:
                if self.send_hotel(hotel, f"Hotels in {location}"):
                    sent_count += 1
            except Exception as e:
                logger.error(f"Error sending hotel to Discord: {e}")

        # Send summary
        self._send_embeds([{
            "title": "✅ Hotel Search Complete",
            "description": f"Sent **{sent_count}** hotel(s) in {location}",
            "color": COLOR_STATUS,
            "timestamp": datetime.utcnow().isoformat(),
        }])

        return sent_count

    def send_trip_summary(
        self,
        origin: str,
        destination: str,
        flights: list[Flight] | list[RoundTrip],
        hotels: list[Hotel],
        nights: int = 1,
    ) -> bool:
        """
        Send a combined trip summary with flights and hotels.

        Args:
            origin: Flight origin
            destination: Destination city
            flights: List of flight options
            hotels: List of hotel options
            nights: Number of nights for price calculation
        """
        if not self._can_send():
            return False

        embeds = [self._build_trip_summary_embed(origin, destination, flights, hotels, nights)]
        return self._send_embeds(embeds)

    # =========================================================================
    # Embed Builders - Ultra Verbose
    # =========================================================================

    def _build_flight_embed(
        self,
        flight: Flight,
        context: Optional[str] = None,
    ) -> dict:
        """Build the main flight overview embed with ALL available fields."""
        # Determine title based on stops
        stops_emoji = "✈️" if flight.stops == 0 else "🔄"
        title = f"{stops_emoji} {flight.origin} → {flight.destination} | ${flight.price:.0f} | {flight.stops_label}"

        # Build description
        desc_parts = []
        if context:
            desc_parts.append(f"**{context}**")
        if flight.origin_city and flight.destination_city:
            desc_parts.append(f"{flight.origin_city} to {flight.destination_city}")
        description = "\n".join(desc_parts) if desc_parts else None

        # All fields
        fields = [
            {"name": "💰 Price", "value": f"${flight.price:.2f} {flight.currency}", "inline": True},
            {"name": "🎯 Stops", "value": flight.stops_label, "inline": True},
            {"name": "⏱️ Duration", "value": flight.duration_formatted, "inline": True},
            {"name": "📅 Departure Date", "value": flight.departure_time.strftime("%A, %B %d, %Y"), "inline": True},
            {"name": "🕐 Departure Time", "value": flight.departure_time.strftime("%I:%M %p"), "inline": True},
            {"name": "🕐 Arrival Time", "value": flight.arrival_time.strftime("%I:%M %p"), "inline": True},
            {"name": "🏙️ Origin", "value": f"{flight.origin}" + (f" ({flight.origin_city})" if flight.origin_city else ""), "inline": True},
            {"name": "🏙️ Destination", "value": f"{flight.destination}" + (f" ({flight.destination_city})" if flight.destination_city else ""), "inline": True},
            {"name": "✈️ Airlines", "value": ", ".join(flight.carriers) if flight.carriers else "Unknown", "inline": True},
        ]

        # Layover info if applicable
        if flight.stops > 0:
            fields.append({
                "name": "🔄 Layover Airports",
                "value": ", ".join(flight.layover_airports) or "N/A",
                "inline": True
            })
            fields.append({
                "name": "⏳ Total Layover Time",
                "value": flight.layover_duration_formatted or "N/A",
                "inline": True
            })

        # Booking link (only include if it's a full URL)
        if flight.deep_link and flight.deep_link.startswith("http"):
            fields.append({
                "name": "🔗 Book Now",
                "value": f"[Click to Book]({flight.deep_link})",
                "inline": True
            })

        # Flight ID
        fields.append({
            "name": "🆔 Flight ID",
            "value": f"`{flight.id[:20]}...`" if len(flight.id) > 20 else f"`{flight.id}`",
            "inline": True
        })

        embed = {
            "title": title,
            "color": self.config.embed_color_flight,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": f"FlightFinder | {flight.departure_time_short} departure"},
        }

        if description:
            embed["description"] = description

        return embed

    def _build_segment_embed(
        self,
        segment: Segment,
        segment_num: int,
        total_segments: int,
        leg_type: str = "",
    ) -> dict:
        """Build a detailed embed for a single flight segment."""
        prefix = f"{leg_type} " if leg_type else ""
        title = f"✈️ {prefix}Segment {segment_num}/{total_segments}: {segment.origin} → {segment.destination}"

        # Flight number
        flight_num = segment.flight_number or "N/A"
        carrier_info = f"{segment.carrier} {flight_num}"
        if segment.carrier_name:
            carrier_info = f"{segment.carrier_name} ({segment.carrier} {flight_num})"

        fields = [
            {"name": "🛫 Carrier", "value": carrier_info, "inline": True},
            {"name": "💺 Cabin Class", "value": segment.cabin_class or "Economy", "inline": True},
            {"name": "⏱️ Duration", "value": f"{segment.duration_minutes // 60}h {segment.duration_minutes % 60}m", "inline": True},
            {
                "name": "🛫 Departure",
                "value": f"**{segment.origin}**" + (f"\n{segment.origin_name}" if segment.origin_name else "") + f"\n{segment.departure_time.strftime('%I:%M %p')}",
                "inline": True
            },
            {
                "name": "🛬 Arrival",
                "value": f"**{segment.destination}**" + (f"\n{segment.destination_name}" if segment.destination_name else "") + f"\n{segment.arrival_time.strftime('%I:%M %p')}",
                "inline": True
            },
            {
                "name": "📅 Date",
                "value": segment.departure_time.strftime("%b %d, %Y"),
                "inline": True
            },
        ]

        return {
            "title": title,
            "color": COLOR_SEGMENT,
            "fields": fields,
        }

    def _build_layover_embeds(self, flight: Flight) -> list[dict]:
        """Build embeds for each layover/connection."""
        embeds = []

        for i in range(len(flight.segments) - 1):
            current_seg = flight.segments[i]
            next_seg = flight.segments[i + 1]

            layover_mins = int((next_seg.departure_time - current_seg.arrival_time).total_seconds() / 60)
            hours = layover_mins // 60
            mins = layover_mins % 60

            airport = current_seg.destination
            airport_name = current_seg.destination_name or airport

            embed = {
                "title": f"🔄 Connection at {airport}",
                "color": COLOR_LAYOVER,
                "fields": [
                    {"name": "🏢 Airport", "value": airport_name, "inline": True},
                    {"name": "⏳ Layover Time", "value": f"{hours}h {mins}m", "inline": True},
                    {"name": "🛬 Arrive", "value": current_seg.arrival_time.strftime("%I:%M %p"), "inline": True},
                    {"name": "🛫 Depart", "value": next_seg.departure_time.strftime("%I:%M %p"), "inline": True},
                    {"name": "📅 Date", "value": current_seg.arrival_time.strftime("%b %d"), "inline": True},
                ],
            }
            embeds.append(embed)

        return embeds

    def _build_roundtrip_summary_embed(
        self,
        roundtrip: RoundTrip,
        context: Optional[str] = None,
    ) -> dict:
        """Build the main round-trip summary embed."""
        out_date = roundtrip.outbound.departure_time.strftime("%b %d")
        in_date = roundtrip.inbound.departure_time.strftime("%b %d")

        title = f"🎫 {roundtrip.origin} ↔ {roundtrip.destination} | ${roundtrip.price:.0f} | {roundtrip.trip_days} days"

        # Destination info
        dest_info = roundtrip.destination
        if roundtrip.destination_city:
            dest_info = f"{roundtrip.destination_city} ({roundtrip.destination})"

        # International status
        int_status = "🌍 International" if roundtrip.is_international else "🏠 Domestic"

        fields = [
            {"name": "💰 Total Price", "value": f"${roundtrip.price:.2f} {roundtrip.currency}", "inline": True},
            {"name": "📅 Trip Dates", "value": f"{out_date} → {in_date}", "inline": True},
            {"name": "📆 Duration", "value": f"{roundtrip.trip_days} days", "inline": True},
            {"name": "🏙️ Destination", "value": dest_info, "inline": True},
            {"name": "🌐 Trip Type", "value": int_status, "inline": True},
            {"name": "✈️ All Airlines", "value": ", ".join(roundtrip.all_carriers) or "Unknown", "inline": True},
            {"name": "⏱️ Total Flight Time", "value": roundtrip.total_travel_formatted, "inline": True},
            {"name": "🛫 Outbound", "value": f"{roundtrip.outbound.stops_label} • {roundtrip.outbound.duration_formatted}", "inline": True},
            {"name": "🛬 Return", "value": f"{roundtrip.inbound.stops_label} • {roundtrip.inbound.duration_formatted}", "inline": True},
        ]

        # Baggage info
        if roundtrip.checked_bag_price:
            fields.append({
                "name": "🧳 Checked Bag",
                "value": f"+${roundtrip.checked_bag_price:.0f}",
                "inline": True
            })
            fields.append({
                "name": "💵 Total with Bag",
                "value": f"${roundtrip.price_with_bag:.0f}",
                "inline": True
            })

        # Booking link (only include if it's a full URL)
        if roundtrip.booking_url and roundtrip.booking_url.startswith("http"):
            fields.append({
                "name": "🔗 Book Now",
                "value": f"[Click to Book]({roundtrip.booking_url})",
                "inline": True
            })

        # Layovers summary
        all_layovers = roundtrip.all_layover_airports
        if all_layovers:
            fields.append({
                "name": "🔄 All Connections",
                "value": ", ".join(all_layovers),
                "inline": True
            })

        embed = {
            "title": title,
            "color": COLOR_ROUNDTRIP,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": f"FlightFinder | ID: {roundtrip.id[:15]}..."},
        }

        if context:
            embed["description"] = f"**{context}**"

        return embed

    def _build_value_analysis_embed(self, roundtrip: RoundTrip) -> dict:
        """Build a value analysis embed for round-trips."""
        fields = [
            {"name": "💰 Total Price", "value": f"${roundtrip.price:.2f}", "inline": True},
            {"name": "📊 Price Per Day", "value": f"${roundtrip.price_per_day:.2f}/day", "inline": True},
            {"name": "📆 Trip Length", "value": f"{roundtrip.trip_days} days", "inline": True},
            {"name": "⏱️ Total Flight Time", "value": f"{roundtrip.total_travel_minutes} mins ({roundtrip.total_travel_formatted})", "inline": True},
            {"name": "🛫 Outbound Stops", "value": f"{roundtrip.outbound.stops}", "inline": True},
            {"name": "🛬 Return Stops", "value": f"{roundtrip.inbound.stops}", "inline": True},
        ]

        if roundtrip.checked_bag_price:
            fields.append({
                "name": "🧳 Bag Price",
                "value": f"${roundtrip.checked_bag_price:.0f}",
                "inline": True
            })
            fields.append({
                "name": "💵 Price with Bag",
                "value": f"${roundtrip.price_with_bag:.0f}",
                "inline": True
            })
            ppd_with_bag = roundtrip.price_with_bag / roundtrip.trip_days if roundtrip.trip_days > 0 else roundtrip.price_with_bag
            fields.append({
                "name": "📊 $/Day with Bag",
                "value": f"${ppd_with_bag:.2f}/day",
                "inline": True
            })

        # Country info
        if roundtrip.destination_country:
            fields.append({
                "name": "🌍 Destination Country",
                "value": roundtrip.destination_country,
                "inline": True
            })

        return {
            "title": "📈 Value Analysis",
            "color": 0x2ECC71,  # Emerald green
            "fields": fields,
        }

    def _build_deal_alert_embed(self, match: AlertMatch) -> dict:
        """Build a prominent deal alert embed."""
        flight = match.flight
        alert = match.alert

        # Calculate savings percentage
        savings_pct = (match.price_delta / alert.max_price) * 100

        if isinstance(flight, RoundTrip):
            title = f"🔥 DEAL ALERT: {flight.origin} ↔ {flight.destination} ${flight.price:.0f}"
            desc = f"A round-trip matching your alert is now available!"
        else:
            title = f"🔥 DEAL ALERT: {flight.origin} → {flight.destination} ${flight.price:.0f}"
            desc = f"A flight matching your alert is now available!"

        if alert.name:
            desc = f"**Alert: {alert.name}**\n\n{desc}"

        fields = [
            {"name": "🎯 Your Max Price", "value": f"${alert.max_price:.0f}", "inline": True},
            {"name": "💰 Current Price", "value": f"${flight.price:.0f}", "inline": True},
            {"name": "💵 You Save", "value": f"${match.price_delta:.0f} ({savings_pct:.1f}%)", "inline": True},
        ]

        if isinstance(flight, RoundTrip):
            fields.extend([
                {"name": "📅 Dates", "value": f"{flight.outbound.departure_time.strftime('%b %d')} - {flight.inbound.departure_time.strftime('%b %d')}", "inline": True},
                {"name": "📆 Trip Length", "value": f"{flight.trip_days} days", "inline": True},
                {"name": "📊 Price/Day", "value": f"${flight.price_per_day:.2f}", "inline": True},
            ])
        else:
            fields.extend([
                {"name": "📅 Date", "value": flight.departure_time.strftime("%b %d, %Y"), "inline": True},
                {"name": "⏱️ Duration", "value": flight.duration_formatted, "inline": True},
                {"name": "🎯 Stops", "value": flight.stops_label, "inline": True},
            ])

        # Booking link (only include if it's a full URL)
        booking_url = flight.booking_url if isinstance(flight, RoundTrip) else flight.deep_link
        if booking_url and booking_url.startswith("http"):
            fields.append({
                "name": "🔗 Book Now",
                "value": f"[**BOOK THIS DEAL**]({booking_url})",
                "inline": False
            })

        return {
            "title": title,
            "description": desc,
            "color": COLOR_DEAL_ALERT,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": f"FlightFinder Deal Alert | Save ${match.price_delta:.0f}!"},
        }

    def _build_search_header_embed(
        self,
        origin: str,
        destination: str,
        result_count: int,
        search_params: Optional[dict] = None,
    ) -> dict:
        """Build a search header embed."""
        dest_display = destination if destination != "anywhere" else "Anywhere"
        title = f"🔍 Search Results: {origin} → {dest_display}"

        fields = [
            {"name": "🛫 Origin", "value": origin, "inline": True},
            {"name": "🛬 Destination", "value": dest_display, "inline": True},
            {"name": "📊 Results Found", "value": str(result_count), "inline": True},
        ]

        if search_params:
            if "max_price" in search_params:
                fields.append({"name": "💰 Max Price", "value": f"${search_params['max_price']}", "inline": True})
            if "max_stops" in search_params:
                fields.append({"name": "🔄 Max Stops", "value": str(search_params['max_stops']), "inline": True})
            if "cabin_class" in search_params:
                fields.append({"name": "💺 Cabin", "value": search_params['cabin_class'], "inline": True})

        return {
            "title": title,
            "color": COLOR_SEARCH_HEADER,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "FlightFinder Search"},
        }

    def _build_search_summary_embed(
        self,
        origin: str,
        destination: str,
        sent_count: int,
    ) -> dict:
        """Build a search completion summary embed."""
        return {
            "title": "✅ Search Complete",
            "description": f"Sent **{sent_count}** flight(s) from {origin} → {destination}",
            "color": COLOR_STATUS,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _build_monitoring_status_embed(
        self,
        alerts: list[PriceAlert],
        last_check: Optional[datetime],
        next_check: Optional[datetime],
        matches_found: int,
    ) -> dict:
        """Build a monitoring status embed."""
        # Build alert list
        alert_lines = []
        for i, alert in enumerate(alerts, 1):
            name = alert.name or f"Alert {i}"
            alert_lines.append(f"• **{name}**: {alert.origin} → {alert.destination} ≤${alert.max_price:.0f}")

        alerts_text = "\n".join(alert_lines) if alert_lines else "No alerts configured"

        fields = [
            {"name": "📋 Active Alerts", "value": str(len(alerts)), "inline": True},
            {"name": "🔔 Matches Found", "value": str(matches_found), "inline": True},
        ]

        if last_check:
            fields.append({
                "name": "🕐 Last Check",
                "value": last_check.strftime("%I:%M %p"),
                "inline": True
            })

        if next_check:
            fields.append({
                "name": "⏰ Next Check",
                "value": next_check.strftime("%I:%M %p"),
                "inline": True
            })

        fields.append({
            "name": "📜 Alert Details",
            "value": alerts_text,
            "inline": False
        })

        return {
            "title": "📊 FlightFinder Monitor Status",
            "color": COLOR_STATUS,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "FlightFinder Monitor"},
        }

    # =========================================================================
    # Internal Methods
    # =========================================================================

    def _can_send(self) -> bool:
        """Check if notifications can be sent."""
        if not self.config.enabled:
            logger.debug("Discord notifications disabled")
            return False

        if not self.config.webhook_url:
            logger.warning("Discord webhook URL not configured")
            return False

        return True

    def _send_embeds(self, embeds: list[dict]) -> bool:
        """
        Send embeds to Discord webhook.

        Discord allows max 10 embeds per message, so we batch them.
        """
        if not embeds:
            return True

        # Rate limiting
        elapsed = time.time() - self._last_send_time
        if elapsed < self.config.rate_limit_delay:
            time.sleep(self.config.rate_limit_delay - elapsed)

        success = True

        # Discord limit: 10 embeds per message
        for i in range(0, len(embeds), 10):
            batch = embeds[i:i + 10]
            payload = {"embeds": batch}

            try:
                response = self._client.post(
                    self.config.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = response.json().get("retry_after", 1)
                    logger.warning(f"Discord rate limited, waiting {retry_after}s")
                    time.sleep(retry_after)
                    response = self._client.post(
                        self.config.webhook_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )

                if response.status_code not in (200, 204):
                    logger.error(f"Discord webhook error: {response.status_code} - {response.text}")
                    success = False
                else:
                    logger.debug(f"Sent {len(batch)} embeds to Discord")

            except Exception as e:
                logger.error(f"Failed to send to Discord: {e}")
                success = False

            self._last_send_time = time.time()

            # Delay between batches
            if i + 10 < len(embeds):
                time.sleep(self.config.rate_limit_delay)

        return success


# Convenience function for quick notifications
def send_to_discord(
    webhook_url: str,
    flight: Flight | RoundTrip | AlertMatch,
    context: Optional[str] = None,
) -> bool:
    """
    Quick helper to send a single flight/deal to Discord.

    Usage:
        from flightfinder.discord import send_to_discord
        send_to_discord("https://discord.com/...", flight)
    """
    with DiscordNotifier(webhook_url=webhook_url) as notifier:
        if isinstance(flight, AlertMatch):
            return notifier.send_deal_alert(flight)
        elif isinstance(flight, RoundTrip):
            return notifier.send_roundtrip(flight, context)
        else:
            return notifier.send_flight(flight, context)
