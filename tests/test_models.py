"""Tests for FlightFinder data models."""

from datetime import datetime

from flightfinder.models import Flight, Location, RoundTrip, Segment


class TestLocation:
    """Tests for Location model."""

    def test_location_creation(self, sample_location):
        """Test basic location creation."""
        assert sample_location.id == "SFO"
        assert sample_location.name == "San Francisco International"
        assert sample_location.type == "AIRPORT"
        assert sample_location.country_code == "US"

    def test_location_str_airport(self, sample_location):
        """Test string representation for airport."""
        result = str(sample_location)
        assert "SFO" in result
        assert "San Francisco" in result

    def test_location_str_city(self):
        """Test string representation for city."""
        loc = Location(
            id="NYC",
            name="New York City",
            slug="new-york",
            type="CITY",
        )
        result = str(loc)
        assert "New York City" in result
        assert "CITY" in result


class TestSegment:
    """Tests for Segment model."""

    def test_segment_creation(self):
        """Test basic segment creation."""
        seg = Segment(
            carrier="UA",
            carrier_name="United Airlines",
            departure_time=datetime(2025, 2, 15, 8, 0),
            arrival_time=datetime(2025, 2, 15, 10, 0),
            origin="SFO",
            destination="LAX",
            duration_minutes=120,
        )
        assert seg.carrier == "UA"
        assert seg.duration_minutes == 120


class TestFlight:
    """Tests for Flight model."""

    def test_flight_creation(self, sample_flight):
        """Test basic flight creation."""
        assert sample_flight.price == 150.0
        assert sample_flight.origin == "SFO"
        assert sample_flight.destination == "LAX"
        assert sample_flight.stops == 0

    def test_duration_formatted(self, sample_flight):
        """Test duration formatting."""
        assert sample_flight.duration_formatted == "2h 0m"

    def test_duration_short(self, sample_flight):
        """Test compact duration format."""
        assert sample_flight.duration_short == "2h"

    def test_duration_short_with_minutes(self):
        """Test compact duration format with minutes."""
        flight = Flight(
            id="test",
            price=100,
            departure_time=datetime.now(),
            arrival_time=datetime.now(),
            origin="SFO",
            destination="LAX",
            duration_minutes=150,
            segments=[],
        )
        assert flight.duration_short == "2h30"

    def test_departure_time_short(self, sample_flight):
        """Test departure time formatting."""
        # 8:00 AM
        result = sample_flight.departure_time_short
        assert "8" in result
        assert "a" in result

    def test_departure_time_short_pm(self):
        """Test PM departure time formatting."""
        flight = Flight(
            id="test",
            price=100,
            departure_time=datetime(2025, 2, 15, 15, 30),
            arrival_time=datetime.now(),
            origin="SFO",
            destination="LAX",
            duration_minutes=120,
            segments=[],
        )
        result = flight.departure_time_short
        assert "3:30p" in result

    def test_carriers(self, sample_flight):
        """Test carrier extraction."""
        carriers = sample_flight.carriers
        assert "United Airlines" in carriers

    def test_stops_label_direct(self, sample_flight):
        """Test stops label for direct flight."""
        assert sample_flight.stops_label == "Direct"

    def test_stops_label_one_stop(self):
        """Test stops label for 1-stop flight."""
        flight = Flight(
            id="test",
            price=100,
            departure_time=datetime.now(),
            arrival_time=datetime.now(),
            origin="SFO",
            destination="LAX",
            duration_minutes=120,
            stops=1,
            segments=[],
        )
        assert flight.stops_label == "1 stop"

    def test_stops_label_multiple(self):
        """Test stops label for multi-stop flight."""
        flight = Flight(
            id="test",
            price=100,
            departure_time=datetime.now(),
            arrival_time=datetime.now(),
            origin="SFO",
            destination="LAX",
            duration_minutes=120,
            stops=2,
            segments=[],
        )
        assert flight.stops_label == "2 stops"

    def test_layover_airports(self):
        """Test layover airport extraction."""
        seg1 = Segment(
            carrier="UA",
            departure_time=datetime(2025, 2, 15, 8, 0),
            arrival_time=datetime(2025, 2, 15, 10, 0),
            origin="SFO",
            destination="DEN",
            duration_minutes=120,
        )
        seg2 = Segment(
            carrier="UA",
            departure_time=datetime(2025, 2, 15, 11, 0),
            arrival_time=datetime(2025, 2, 15, 13, 0),
            origin="DEN",
            destination="LAX",
            duration_minutes=120,
        )
        flight = Flight(
            id="test",
            price=200,
            departure_time=seg1.departure_time,
            arrival_time=seg2.arrival_time,
            origin="SFO",
            destination="LAX",
            duration_minutes=300,
            stops=1,
            segments=[seg1, seg2],
        )
        assert flight.layover_airports == ["DEN"]

    def test_flight_str(self, sample_flight):
        """Test flight string representation."""
        result = str(sample_flight)
        assert "$150" in result
        assert "SFO" in result
        assert "LAX" in result


class TestRoundTrip:
    """Tests for RoundTrip model."""

    def test_roundtrip_trip_days(self):
        """Test trip duration calculation."""
        outbound = Flight(
            id="out",
            price=0,
            departure_time=datetime(2025, 2, 15, 8, 0),
            arrival_time=datetime(2025, 2, 15, 10, 0),
            origin="SFO",
            destination="LAX",
            duration_minutes=120,
            segments=[],
        )
        inbound = Flight(
            id="in",
            price=0,
            departure_time=datetime(2025, 2, 22, 18, 0),
            arrival_time=datetime(2025, 2, 22, 20, 0),
            origin="LAX",
            destination="SFO",
            duration_minutes=120,
            segments=[],
        )
        rt = RoundTrip(
            id="rt1",
            price=350,
            outbound=outbound,
            inbound=inbound,
        )
        assert rt.trip_days == 7

    def test_roundtrip_price_with_bag(self):
        """Test price with checked bag."""
        outbound = Flight(
            id="out",
            price=0,
            departure_time=datetime(2025, 2, 15, 8, 0),
            arrival_time=datetime(2025, 2, 15, 10, 0),
            origin="SFO",
            destination="LAX",
            duration_minutes=120,
            segments=[],
        )
        inbound = Flight(
            id="in",
            price=0,
            departure_time=datetime(2025, 2, 22, 18, 0),
            arrival_time=datetime(2025, 2, 22, 20, 0),
            origin="LAX",
            destination="SFO",
            duration_minutes=120,
            segments=[],
        )
        rt = RoundTrip(
            id="rt1",
            price=350,
            outbound=outbound,
            inbound=inbound,
            checked_bag_price=35,
        )
        assert rt.price_with_bag == 385

    def test_roundtrip_is_domestic(self):
        """Test domestic flight detection."""
        outbound = Flight(
            id="out",
            price=0,
            departure_time=datetime.now(),
            arrival_time=datetime.now(),
            origin="SFO",
            destination="LAX",
            duration_minutes=120,
            segments=[],
        )
        inbound = Flight(
            id="in",
            price=0,
            departure_time=datetime.now(),
            arrival_time=datetime.now(),
            origin="LAX",
            destination="SFO",
            duration_minutes=120,
            segments=[],
        )
        rt = RoundTrip(
            id="rt1",
            price=350,
            outbound=outbound,
            inbound=inbound,
            destination_country="US",
        )
        assert rt.is_domestic is True
        assert rt.is_international is False

    def test_roundtrip_is_international(self):
        """Test international flight detection."""
        outbound = Flight(
            id="out",
            price=0,
            departure_time=datetime.now(),
            arrival_time=datetime.now(),
            origin="SFO",
            destination="NRT",
            duration_minutes=720,
            segments=[],
        )
        inbound = Flight(
            id="in",
            price=0,
            departure_time=datetime.now(),
            arrival_time=datetime.now(),
            origin="NRT",
            destination="SFO",
            duration_minutes=720,
            segments=[],
        )
        rt = RoundTrip(
            id="rt1",
            price=800,
            outbound=outbound,
            inbound=inbound,
            destination_country="JP",
        )
        assert rt.is_international is True
        assert rt.is_domestic is False
