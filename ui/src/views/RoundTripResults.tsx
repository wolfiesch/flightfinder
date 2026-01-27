import { useState, useMemo } from 'react';
import type { RoundTripSearchResult } from '@/types/flightfinder';
import { RoundTripCard } from '@/components/FlightCard';
import { FlightFilters, FlightSortOption } from '@/components/SearchFilters';
import { getInjectedData } from '@/utils/mcpBridge';

/**
 * View for displaying round-trip flight search results.
 */
export function RoundTripResultsView() {
  const data = getInjectedData<RoundTripSearchResult>();

  const [maxStops, setMaxStops] = useState<number | null>(null);
  const [sortBy, setSortBy] = useState<FlightSortOption>('price');

  const filteredAndSorted = useMemo(() => {
    if (!data?.roundtrips) return [];

    let trips = [...data.roundtrips];

    // Filter by max stops (applies to both legs)
    if (maxStops !== null) {
      trips = trips.filter(
        (t) => t.outbound_stops <= maxStops && t.return_stops <= maxStops
      );
    }

    // Sort
    trips.sort((a, b) => {
      switch (sortBy) {
        case 'price':
          return a.price - b.price;
        case 'duration':
          return a.trip_days - b.trip_days;
        case 'departure':
          return a.outbound_date.localeCompare(b.outbound_date);
        default:
          return 0;
      }
    });

    return trips;
  }, [data?.roundtrips, maxStops, sortBy]);

  if (!data) {
    return (
      <div className="p-6 text-center text-ff-text-secondary">
        No round-trip data available
      </div>
    );
  }

  return (
    <div className="p-4 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold gradient-text mb-2">
          Round Trips: {data.search.origin} → {data.search.destination}
        </h1>
        <p className="text-ff-text-secondary">
          Departing around {data.search.depart_around} • {data.search.trip_duration} •{' '}
          {data.count} result{data.count !== 1 ? 's' : ''} found
        </p>
      </div>

      {/* Filters */}
      <FlightFilters
        maxStops={maxStops}
        onMaxStopsChange={setMaxStops}
        sortBy={sortBy}
        onSortChange={setSortBy}
      />

      {/* Results Count */}
      {maxStops !== null && filteredAndSorted.length !== data.roundtrips.length && (
        <p className="text-ff-text-dim text-sm mb-4">
          Showing {filteredAndSorted.length} of {data.roundtrips.length} round trips
        </p>
      )}

      {/* Results Grid */}
      {filteredAndSorted.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2">
          {filteredAndSorted.map((trip, idx) => (
            <RoundTripCard key={`trip-${idx}`} roundtrip={trip} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-ff-text-secondary">
          No round trips match your filters.
          <button
            onClick={() => setMaxStops(null)}
            className="block mx-auto mt-4 text-ff-cyan hover:underline"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  );
}

export default RoundTripResultsView;
