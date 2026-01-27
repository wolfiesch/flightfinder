import { useState, useMemo } from 'react';
import type { HotelSearchResult } from '@/types/flightfinder';
import { HotelCard } from '@/components/HotelCard';
import { HotelFilters, HotelSortOption } from '@/components/SearchFilters';
import { getInjectedData } from '@/utils/mcpBridge';

/**
 * View for displaying hotel search results.
 */
export function HotelResultsView() {
  const data = getInjectedData<HotelSearchResult>();

  const [minRating, setMinRating] = useState<number | null>(null);
  const [sortBy, setSortBy] = useState<HotelSortOption>('price');

  const filteredAndSorted = useMemo(() => {
    if (!data?.hotels) return [];

    let hotels = [...data.hotels];

    // Filter by min rating
    if (minRating !== null) {
      hotels = hotels.filter((h) => h.rating != null && h.rating >= minRating);
    }

    // Sort
    hotels.sort((a, b) => {
      switch (sortBy) {
        case 'price':
          return (a.min_price ?? Infinity) - (b.min_price ?? Infinity);
        case 'rating':
          return (b.rating ?? 0) - (a.rating ?? 0);
        case 'reviews':
          return (b.review_count ?? 0) - (a.review_count ?? 0);
        default:
          return 0;
      }
    });

    return hotels;
  }, [data?.hotels, minRating, sortBy]);

  if (!data) {
    return (
      <div className="p-6 text-center text-ff-text-secondary">
        No hotel data available
      </div>
    );
  }

  return (
    <div className="p-4 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold gradient-text mb-2">
          Hotels in {data.location}
        </h1>
        <p className="text-ff-text-secondary">
          {data.count} of {data.total_available} hotels shown
        </p>
      </div>

      {/* Filters */}
      <HotelFilters
        minRating={minRating}
        onMinRatingChange={setMinRating}
        sortBy={sortBy}
        onSortChange={setSortBy}
      />

      {/* Results Count */}
      {minRating !== null && filteredAndSorted.length !== data.hotels.length && (
        <p className="text-ff-text-dim text-sm mb-4">
          Showing {filteredAndSorted.length} of {data.hotels.length} hotels
        </p>
      )}

      {/* Results Grid */}
      {filteredAndSorted.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2">
          {filteredAndSorted.map((hotel, idx) => (
            <HotelCard key={`hotel-${idx}`} hotel={hotel} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-ff-text-secondary">
          No hotels match your filters.
          <button
            onClick={() => setMinRating(null)}
            className="block mx-auto mt-4 text-ff-cyan hover:underline"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  );
}

export default HotelResultsView;
