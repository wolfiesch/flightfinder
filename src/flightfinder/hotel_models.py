"""Data models for hotel search results."""

from datetime import date

from pydantic import BaseModel, Field


class HotelLocation(BaseModel):
    """Geographic location of a hotel."""

    latitude: float
    longitude: float


class HotelReviewSummary(BaseModel):
    """Summary of hotel reviews from TripAdvisor."""

    rating: float = Field(ge=0, le=5, description="Average rating out of 5")
    count: int = Field(ge=0, description="Number of reviews")

    @property
    def rating_label(self) -> str:
        """Human-readable rating label."""
        if self.rating >= 4.5:
            return "Excellent"
        elif self.rating >= 4.0:
            return "Very Good"
        elif self.rating >= 3.5:
            return "Good"
        elif self.rating >= 3.0:
            return "Average"
        return "Below Average"


class HotelPriceRange(BaseModel):
    """Price range for a hotel (min/max nightly rates)."""

    minimum: float
    maximum: float
    currency: str = "USD"

    @property
    def midpoint(self) -> float:
        """Approximate midpoint price."""
        return (self.minimum + self.maximum) / 2

    def __str__(self) -> str:
        return f"${self.minimum:.0f}-${self.maximum:.0f}"


class Hotel(BaseModel):
    """A hotel/accommodation from search results."""

    key: str = Field(description="Unique hotel key (e.g., 'g60763-d23448880')")
    name: str
    accommodation_type: str = Field(description="Hotel, Hostel, Ryokan, etc.")
    url: str | None = None
    review_summary: HotelReviewSummary | None = None
    price_range: HotelPriceRange | None = None
    location: HotelLocation | None = None
    image_url: str | None = None
    mentions: list[str] = Field(default_factory=list, description="Tags like 'Modern', 'Business'")
    labels: list[str] = Field(default_factory=list, description="Badges like 'Best seller'")

    @property
    def rating(self) -> float | None:
        """Shortcut to review rating."""
        return self.review_summary.rating if self.review_summary else None

    @property
    def review_count(self) -> int | None:
        """Shortcut to review count."""
        return self.review_summary.count if self.review_summary else None

    @property
    def min_price(self) -> float | None:
        """Shortcut to minimum nightly price."""
        return self.price_range.minimum if self.price_range else None

    @property
    def max_price(self) -> float | None:
        """Shortcut to maximum nightly price."""
        return self.price_range.maximum if self.price_range else None

    @property
    def tripadvisor_id(self) -> str | None:
        """Extract TripAdvisor hotel ID from the key."""
        if "-d" in self.key:
            return self.key.split("-d")[1]
        return None

    @property
    def location_id(self) -> str | None:
        """Extract location ID from the key."""
        if self.key.startswith("g"):
            return self.key.split("-")[0]
        return None

    def __str__(self) -> str:
        price_str = str(self.price_range) if self.price_range else "N/A"
        rating_str = f"{self.rating:.1f}" if self.rating else "N/A"
        return f"{self.name} ({self.accommodation_type}) - {price_str}/night - {rating_str}/5"


class HotelRate(BaseModel):
    """A specific rate/price from an OTA (Online Travel Agency)."""

    provider: str = Field(description="OTA name like 'Booking.com', 'Expedia'")
    price: float
    currency: str = "USD"
    room_type: str | None = None
    is_refundable: bool | None = None
    url: str | None = None

    def __str__(self) -> str:
        return f"${self.price:.0f} via {self.provider}"


class HotelRates(BaseModel):
    """Collection of rates for a specific hotel stay."""

    hotel_key: str
    check_in: date
    check_out: date
    currency: str = "USD"
    rates: list[HotelRate] = Field(default_factory=list)

    @property
    def nights(self) -> int:
        """Number of nights for this stay."""
        return (self.check_out - self.check_in).days

    @property
    def cheapest(self) -> HotelRate | None:
        """Get the cheapest rate."""
        if not self.rates:
            return None
        return min(self.rates, key=lambda r: r.price)

    @property
    def cheapest_price(self) -> float | None:
        """Get the cheapest price."""
        rate = self.cheapest
        return rate.price if rate else None

    @property
    def price_per_night(self) -> float | None:
        """Cheapest price per night."""
        if self.cheapest_price and self.nights > 0:
            return self.cheapest_price / self.nights
        return None


class HotelSearchResults(BaseModel):
    """Results from a hotel list/search query."""

    location_key: str
    total_count: int
    hotels: list[Hotel] = Field(default_factory=list)
    offset: int = 0
    limit: int = 30

    @property
    def has_more(self) -> bool:
        """Check if there are more results available."""
        return self.offset + len(self.hotels) < self.total_count


# Common location keys for major cities
LOCATION_KEYS = {
    # United States
    "new york": "g60763",
    "nyc": "g60763",
    "los angeles": "g32655",
    "la": "g32655",
    "san francisco": "g60713",
    "sf": "g60713",
    "chicago": "g35805",
    "las vegas": "g45963",
    "miami": "g34438",
    "seattle": "g60878",
    "boston": "g60745",
    "washington dc": "g28970",
    "dc": "g28970",
    "austin": "g30196",
    "denver": "g33388",
    "san diego": "g60750",
    "portland": "g52024",
    "phoenix": "g31310",
    "atlanta": "g60898",
    "nashville": "g55229",
    "new orleans": "g60864",
    "orlando": "g34515",
    "honolulu": "g60982",
    "hawaii": "g60982",
    # International
    "london": "g186338",
    "paris": "g187147",
    "tokyo": "g298184",
    "rome": "g187791",
    "barcelona": "g187497",
    "amsterdam": "g188590",
    "berlin": "g187323",
    "dubai": "g295424",
    "singapore": "g294265",
    "hong kong": "g294217",
    "bangkok": "g293916",
    "sydney": "g255060",
    "melbourne": "g255100",
    "toronto": "g155019",
    "vancouver": "g154943",
    "montreal": "g155032",
    "mexico city": "g150800",
    "cancun": "g150807",
    "lisbon": "g189158",
    "madrid": "g187514",
    "prague": "g274707",
    "vienna": "g190454",
    "dublin": "g186605",
    "edinburgh": "g186525",
    "florence": "g187895",
    "venice": "g187870",
    "milan": "g187849",
    "munich": "g187309",
    "zurich": "g188113",
    "copenhagen": "g189541",
    "stockholm": "g189852",
    "oslo": "g190479",
    "reykjavik": "g189970",
    "athens": "g189400",
    "istanbul": "g293974",
    "cairo": "g294201",
    "cape town": "g1722390",
    "marrakech": "g293734",
    "bali": "g294226",
    "seoul": "g294197",
    "taipei": "g293913",
    "kuala lumpur": "g298570",
    "buenos aires": "g312741",
    "rio de janeiro": "g303506",
    "lima": "g294316",
    "bogota": "g294074",
    "santiago": "g294305",
    # Japan (common destinations)
    "kyoto": "g298564",
    "osaka": "g298566",
}


def get_location_key(city: str) -> str | None:
    """
    Get a TripAdvisor location key for a city name.

    Args:
        city: City name (case-insensitive)

    Returns:
        Location key like 'g60763' or None if not found
    """
    return LOCATION_KEYS.get(city.lower().strip())


def parse_location_key_from_url(url: str) -> str | None:
    """
    Extract a location key from a TripAdvisor Hotels URL.

    Example:
        https://www.tripadvisor.com/Hotels-g60763-New_York_City-Hotels.html
        -> 'g60763'
    """
    import re

    match = re.search(r"Hotels-(g\d+)-", url)
    if match:
        return match.group(1)
    return None
