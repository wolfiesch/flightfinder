import type { LocationSearchResult } from '@/types/flightfinder';
import { LocationList } from '@/components/LocationCard';
import { getInjectedData } from '@/utils/mcpBridge';

/**
 * View for displaying location search results.
 */
export function LocationResultsView() {
  const data = getInjectedData<LocationSearchResult>();

  if (!data) {
    return (
      <div className="p-6 text-center text-ff-text-secondary">
        No location data available
      </div>
    );
  }

  return (
    <div className="p-4 max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold gradient-text mb-2">
          Locations matching "{data.query}"
        </h1>
        <p className="text-ff-text-secondary">
          {data.count} result{data.count !== 1 ? 's' : ''} found • Click to search flights
        </p>
      </div>

      {/* Results */}
      <LocationList locations={data.locations} />
    </div>
  );
}

export default LocationResultsView;
