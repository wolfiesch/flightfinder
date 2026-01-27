import type { Location } from '@/types/flightfinder';
import { sendPrompt } from '@/utils/mcpBridge';

interface LocationCardProps {
  location: Location;
  onSelect?: (location: Location) => void;
}

/**
 * Get icon for location type.
 */
function getLocationIcon(type: string): string {
  switch (type) {
    case 'AIRPORT':
      return '✈️';
    case 'CITY':
      return '🏙️';
    case 'COUNTRY':
      return '🌍';
    default:
      return '📍';
  }
}

/**
 * Card component for displaying a location search result.
 */
export function LocationCard({ location, onSelect }: LocationCardProps) {
  const handleClick = () => {
    // When clicked, send a prompt to search flights from/to this location
    sendPrompt(`Search flights to ${location.code}`);
    onSelect?.(location);
  };

  return (
    <button
      onClick={handleClick}
      className="w-full text-left bg-ff-bg-secondary border border-ff-terminal-border rounded-lg p-4 hover:border-ff-purple/50 transition-colors card-glow"
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <span className="text-2xl">{getLocationIcon(location.type)}</span>

        {/* Details */}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg font-bold text-ff-cyan">{location.code}</span>
            <span className="px-2 py-0.5 text-xs bg-ff-terminal rounded border border-ff-terminal-border text-ff-text-secondary">
              {location.type}
            </span>
          </div>
          <div className="text-ff-text-primary">{location.name}</div>
          {(location.city || location.country) && (
            <div className="text-ff-text-secondary text-sm">
              {[location.city, location.country].filter(Boolean).join(', ')}
            </div>
          )}
        </div>

        {/* Arrow */}
        <span className="text-ff-text-dim">→</span>
      </div>
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

interface LocationListProps {
  locations: Location[];
  onSelect?: (location: Location) => void;
}

/**
 * List of location cards.
 */
export function LocationList({ locations, onSelect }: LocationListProps) {
  if (locations.length === 0) {
    return (
      <div className="text-center py-8 text-ff-text-secondary">
        No locations found
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {locations.map((location) => (
        <LocationCard
          key={`${location.type}-${location.code}`}
          location={location}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}
