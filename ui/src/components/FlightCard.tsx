import type { Flight, RoundTrip } from '@/types/flightfinder';
import { formatPrice, formatStops, formatDateTime, openLink } from '@/utils/mcpBridge';

interface FlightCardProps {
  flight: Flight;
  onBook?: () => void;
}

/**
 * Card component for displaying a one-way flight option.
 */
export function FlightCard({ flight, onBook }: FlightCardProps) {
  const handleBook = () => {
    if (flight.booking_url) {
      openLink(flight.booking_url);
    }
    onBook?.();
  };

  return (
    <div className="bg-ff-bg-secondary border border-ff-terminal-border rounded-lg p-4 hover:border-ff-purple/50 transition-colors card-glow">
      {/* Header: Price and Route */}
      <div className="flex justify-between items-start mb-3">
        <div>
          <span className="text-2xl font-bold gradient-text">
            {formatPrice(flight.price)}
          </span>
        </div>
        <div className="text-right">
          <div className="text-ff-text-primary font-medium">
            {flight.origin} → {flight.destination}
          </div>
          <div className="text-ff-text-secondary text-sm">
            {formatStops(flight.stops)}
          </div>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
        <div>
          <div className="text-ff-text-dim">Departure</div>
          <div className="text-ff-text-primary">{formatDateTime(flight.departure)}</div>
        </div>
        <div>
          <div className="text-ff-text-dim">Duration</div>
          <div className="text-ff-text-primary">{flight.duration}</div>
        </div>
      </div>

      {/* Carriers */}
      {flight.carriers.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {flight.carriers.map((carrier, idx) => (
            <span
              key={idx}
              className="px-2 py-0.5 text-xs bg-ff-terminal rounded border border-ff-terminal-border text-ff-text-secondary"
            >
              {carrier}
            </span>
          ))}
        </div>
      )}

      {/* Book Button */}
      {flight.booking_url && (
        <button
          onClick={handleBook}
          className="w-full py-2 px-4 bg-gradient-horizontal rounded-lg font-medium text-white hover:opacity-90 transition-opacity"
        >
          Book Flight
        </button>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

interface RoundTripCardProps {
  roundtrip: RoundTrip;
  onBook?: () => void;
}

/**
 * Card component for displaying a round-trip flight option.
 */
export function RoundTripCard({ roundtrip, onBook }: RoundTripCardProps) {
  const handleBook = () => {
    if (roundtrip.booking_url) {
      openLink(roundtrip.booking_url);
    }
    onBook?.();
  };

  return (
    <div className="bg-ff-bg-secondary border border-ff-terminal-border rounded-lg p-4 hover:border-ff-purple/50 transition-colors card-glow">
      {/* Header: Prices */}
      <div className="flex justify-between items-start mb-3">
        <div>
          <span className="text-2xl font-bold gradient-text">
            {formatPrice(roundtrip.price)}
          </span>
          {roundtrip.price_with_bag > roundtrip.price && (
            <span className="text-ff-text-dim text-sm ml-2">
              ({formatPrice(roundtrip.price_with_bag)} w/ bag)
            </span>
          )}
        </div>
        <div className="text-right">
          <div className="text-ff-text-primary font-medium">
            {roundtrip.origin} → {roundtrip.destination}
          </div>
          {roundtrip.destination_city && (
            <div className="text-ff-text-secondary text-sm">
              {roundtrip.destination_city}
            </div>
          )}
        </div>
      </div>

      {/* Trip Details Grid */}
      <div className="grid grid-cols-3 gap-3 mb-4 text-sm">
        <div>
          <div className="text-ff-text-dim">Outbound</div>
          <div className="text-ff-text-primary">{roundtrip.outbound_date}</div>
          <div className="text-ff-text-secondary text-xs">
            {formatStops(roundtrip.outbound_stops)}
          </div>
        </div>
        <div>
          <div className="text-ff-text-dim">Return</div>
          <div className="text-ff-text-primary">{roundtrip.return_date}</div>
          <div className="text-ff-text-secondary text-xs">
            {formatStops(roundtrip.return_stops)}
          </div>
        </div>
        <div>
          <div className="text-ff-text-dim">Duration</div>
          <div className="text-ff-text-primary">{roundtrip.trip_days} days</div>
        </div>
      </div>

      {/* Carriers */}
      {roundtrip.carriers.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {roundtrip.carriers.map((carrier, idx) => (
            <span
              key={idx}
              className="px-2 py-0.5 text-xs bg-ff-terminal rounded border border-ff-terminal-border text-ff-text-secondary"
            >
              {carrier}
            </span>
          ))}
        </div>
      )}

      {/* Book Button */}
      {roundtrip.booking_url && (
        <button
          onClick={handleBook}
          className="w-full py-2 px-4 bg-gradient-horizontal rounded-lg font-medium text-white hover:opacity-90 transition-opacity"
        >
          Book Round Trip
        </button>
      )}
    </div>
  );
}
