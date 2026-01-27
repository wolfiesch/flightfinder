import { useState, useMemo } from 'react';
import type { FlightSearchResult } from '@/types/flightfinder';
import { FlightCard } from '@/components/FlightCard';
import { FlightFilters, FlightSortOption } from '@/components/SearchFilters';
import { getInjectedData } from '@/utils/mcpBridge';

/**
 * Parse duration string like "5h 30m" to minutes.
 */
function parseDuration(duration: string): number {
  const match = duration.match(/(\d+)h\s*(\d+)?m?/);
  if (!match) return 0;
  const hours = parseInt(match[1], 10);
  const minutes = parseInt(match[2] || '0', 10);
  return hours * 60 + minutes;
}

/**
 * View for displaying one-way flight search results.
 */
export function FlightResultsView() {
  const data = getInjectedData<FlightSearchResult>();

  const [maxStops, setMaxStops] = useState<number | null>(null);
  const [sortBy, setSortBy] = useState<FlightSortOption>('price');

  const filteredAndSorted = useMemo(() => {
    if (!data?.flights) return [];

    let flights = [...data.flights];

    // Filter by max stops
    if (maxStops !== null) {
      flights = flights.filter((f) => f.stops <= maxStops);
    }

    // Sort
    flights.sort((a, b) => {
      switch (sortBy) {
        case 'price':
          return a.price - b.price;
        case 'duration':
          return parseDuration(a.duration) - parseDuration(b.duration);
        case 'departure':
          return new Date(a.departure).getTime() - new Date(b.departure).getTime();
        default:
          return 0;
      }
    });

    return flights;
  }, [data?.flights, maxStops, sortBy]);

  if (!data) {
    return (
      <div className="p-6 text-center text-ff-text-secondary">
        No flight data available
      </div>
    );
  }

  return (
    <div className="p-4 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold gradient-text mb-2">
          Flights: {data.search.origin} → {data.search.destination}
        </h1>
        <p className="text-ff-text-secondary">
          {data.search.dates} • {data.count} result{data.count !== 1 ? 's' : ''} found
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
      {maxStops !== null && filteredAndSorted.length !== data.flights.length && (
        <p className="text-ff-text-dim text-sm mb-4">
          Showing {filteredAndSorted.length} of {data.flights.length} flights
        </p>
      )}

      {/* Results Grid */}
      {filteredAndSorted.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2">
          {filteredAndSorted.map((flight, idx) => (
            <FlightCard key={`flight-${idx}`} flight={flight} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-ff-text-secondary">
          No flights match your filters.
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

export default FlightResultsView;
