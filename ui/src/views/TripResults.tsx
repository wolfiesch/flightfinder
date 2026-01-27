import type { TripSearchResult } from '@/types/flightfinder';
import { TripHotelCard } from '@/components/HotelCard';
import { getInjectedData, formatPrice } from '@/utils/mcpBridge';

/**
 * View for displaying combined trip (flight + hotel) search results.
 */
export function TripResultsView() {
  const data = getInjectedData<TripSearchResult>();

  if (!data) {
    return (
      <div className="p-6 text-center text-ff-text-secondary">
        No trip data available
      </div>
    );
  }

  const hasFlights = data.flights.length > 0;
  const hasHotels = data.hotels.length > 0;

  return (
    <div className="p-4 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold gradient-text mb-2">
          Trip to {data.destination}
        </h1>
        <p className="text-ff-text-secondary">
          From {data.origin} • Departing around {data.dates.depart_around} •{' '}
          {data.dates.nights} nights
        </p>
      </div>

      {/* Estimated Total */}
      {data.estimated_total && (
        <div className="bg-ff-bg-secondary border border-ff-purple/30 rounded-lg p-4 mb-6">
          <h2 className="text-lg font-semibold text-ff-text-primary mb-3">
            Estimated Trip Cost
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-ff-text-dim text-sm">Flights</div>
              <div className="text-xl font-bold text-ff-cyan">
                {formatPrice(data.estimated_total.flight)}
              </div>
            </div>
            <div>
              <div className="text-ff-text-dim text-sm">
                Hotels ({data.estimated_total.nights} nights)
              </div>
              <div className="text-xl font-bold text-ff-purple">
                {formatPrice(data.estimated_total.hotel_total)}
              </div>
              <div className="text-ff-text-secondary text-xs">
                {formatPrice(data.estimated_total.hotel_per_night)}/night
              </div>
            </div>
            <div className="col-span-2 md:col-span-1 md:col-start-4">
              <div className="text-ff-text-dim text-sm">Total</div>
              <div className="text-2xl font-bold gradient-text">
                {formatPrice(data.estimated_total.total)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Two Column Layout */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Flights Column */}
        <div>
          <h2 className="text-lg font-semibold text-ff-text-primary mb-4 flex items-center gap-2">
            <span className="text-ff-cyan">✈️</span> Flights
          </h2>
          {data.flight_error && (
            <div className="bg-ff-error/10 border border-ff-error/30 rounded-lg p-3 mb-4 text-ff-error text-sm">
              {data.flight_error}
            </div>
          )}
          {hasFlights ? (
            <div className="space-y-3">
              {data.flights.map((flight, idx) => (
                <div
                  key={idx}
                  className="bg-ff-bg-secondary border border-ff-terminal-border rounded-lg p-3"
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xl font-bold gradient-text">
                      {formatPrice(flight.price)}
                    </span>
                    <span className="text-ff-text-secondary text-sm">
                      {flight.trip_days} days
                    </span>
                  </div>
                  <div className="text-ff-text-primary text-sm mb-2">
                    {flight.dates}
                  </div>
                  {flight.carriers.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {flight.carriers.map((carrier, cidx) => (
                        <span
                          key={cidx}
                          className="px-2 py-0.5 text-xs bg-ff-terminal rounded border border-ff-terminal-border text-ff-text-secondary"
                        >
                          {carrier}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-ff-text-dim text-center py-8">
              No flights found
            </div>
          )}
        </div>

        {/* Hotels Column */}
        <div>
          <h2 className="text-lg font-semibold text-ff-text-primary mb-4 flex items-center gap-2">
            <span className="text-ff-purple">🏨</span> Hotels
          </h2>
          {data.hotel_error && (
            <div className="bg-ff-error/10 border border-ff-error/30 rounded-lg p-3 mb-4 text-ff-error text-sm">
              {data.hotel_error}
            </div>
          )}
          {data.hotel_note && (
            <div className="bg-ff-warning/10 border border-ff-warning/30 rounded-lg p-3 mb-4 text-ff-warning text-sm">
              {data.hotel_note}
            </div>
          )}
          {hasHotels ? (
            <div className="space-y-3">
              {data.hotels.map((hotel, idx) => (
                <TripHotelCard
                  key={idx}
                  hotel={hotel}
                  nights={data.dates.nights}
                />
              ))}
            </div>
          ) : (
            <div className="text-ff-text-dim text-center py-8">
              No hotels found
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default TripResultsView;
