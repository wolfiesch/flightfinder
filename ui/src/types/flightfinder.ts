/**
 * TypeScript types mirroring Python Pydantic models in flightfinder.
 * Keep in sync with src/flightfinder/models.py and hotel_models.py
 */

// ─────────────────────────────────────────────────────────────────────────────
// Location Types
// ─────────────────────────────────────────────────────────────────────────────

export interface Location {
  code: string;
  name: string;
  type: 'AIRPORT' | 'CITY' | 'COUNTRY';
  city?: string | null;
  country?: string | null;
  country_code?: string | null;
}

export interface LocationSearchResult {
  count: number;
  query: string;
  locations: Location[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Flight Types
// ─────────────────────────────────────────────────────────────────────────────

export interface Segment {
  carrier: string;
  carrier_name?: string | null;
  flight_number?: string | null;
  departure_time: string; // ISO datetime
  arrival_time: string;   // ISO datetime
  origin: string;
  origin_name?: string | null;
  destination: string;
  destination_name?: string | null;
  duration_minutes: number;
}

export interface Flight {
  price: number;
  origin: string;
  destination: string;
  departure: string;      // ISO datetime
  arrival: string;        // ISO datetime
  duration: string;       // Formatted like "5h 30m"
  stops: number;
  carriers: string[];
  booking_url?: string | null;
}

export interface FlightSearchResult {
  count: number;
  search: {
    origin: string;
    destination: string;
    dates: string;
  };
  flights: Flight[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Round Trip Types
// ─────────────────────────────────────────────────────────────────────────────

export interface RoundTrip {
  price: number;
  price_with_bag: number;
  origin: string;
  destination: string;
  destination_city?: string | null;
  outbound_date: string;  // ISO date
  return_date: string;    // ISO date
  trip_days: number;
  outbound_stops: number;
  return_stops: number;
  carriers: string[];
  booking_url?: string | null;
}

export interface RoundTripSearchResult {
  count: number;
  search: {
    origin: string;
    destination: string;
    depart_around: string;
    trip_duration: string;
  };
  roundtrips: RoundTrip[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Hotel Types
// ─────────────────────────────────────────────────────────────────────────────

export interface Hotel {
  name: string;
  type: string;
  price_range?: string | null;
  min_price?: number | null;
  max_price?: number | null;
  rating?: number | null;
  review_count?: number | null;
  url?: string | null;
  highlights: string[];
}

export interface HotelSearchResult {
  count: number;
  total_available: number;
  location: string;
  hotels: Hotel[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Trip Types (Combined Flight + Hotel)
// ─────────────────────────────────────────────────────────────────────────────

export interface TripFlight {
  price: number;
  dates: string;
  trip_days: number;
  carriers: string[];
}

export interface TripHotel {
  name: string;
  price_per_night?: number | null;
  rating?: number | null;
  type: string;
}

export interface EstimatedTotal {
  flight: number;
  hotel_per_night: number;
  hotel_total: number;
  total: number;
  nights: number;
}

export interface TripSearchResult {
  origin: string;
  destination: string;
  dates: {
    depart_around: string;
    nights: number;
  };
  flights: TripFlight[];
  hotels: TripHotel[];
  estimated_total?: EstimatedTotal | null;
  flight_error?: string;
  hotel_error?: string;
  hotel_note?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Injected Data Types (from Python server)
// ─────────────────────────────────────────────────────────────────────────────

export type FlightFinderData =
  | FlightSearchResult
  | RoundTripSearchResult
  | HotelSearchResult
  | TripSearchResult
  | LocationSearchResult;

// Extend Window to include injected data
declare global {
  interface Window {
    __FLIGHTFINDER_DATA__?: FlightFinderData;
  }
}
