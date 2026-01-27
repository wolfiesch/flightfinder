import type { Hotel, TripHotel } from '@/types/flightfinder';
import { formatPrice, openLink } from '@/utils/mcpBridge';

interface HotelCardProps {
  hotel: Hotel;
  onViewDeal?: () => void;
}

/**
 * Render star rating as visual stars.
 */
function StarRating({ rating }: { rating: number | null | undefined }) {
  if (rating == null) return <span className="text-ff-text-dim">No rating</span>;

  const fullStars = Math.floor(rating);
  const hasHalf = rating % 1 >= 0.5;
  const emptyStars = 5 - fullStars - (hasHalf ? 1 : 0);

  return (
    <div className="flex items-center gap-0.5">
      {Array(fullStars)
        .fill(0)
        .map((_, i) => (
          <span key={`full-${i}`} className="text-ff-warning">★</span>
        ))}
      {hasHalf && <span className="text-ff-warning">☆</span>}
      {Array(emptyStars)
        .fill(0)
        .map((_, i) => (
          <span key={`empty-${i}`} className="text-ff-text-dim">☆</span>
        ))}
      <span className="ml-1 text-ff-text-secondary text-sm">
        ({rating.toFixed(1)})
      </span>
    </div>
  );
}

/**
 * Card component for displaying a hotel option.
 */
export function HotelCard({ hotel, onViewDeal }: HotelCardProps) {
  const handleViewDeal = () => {
    if (hotel.url) {
      openLink(hotel.url);
    }
    onViewDeal?.();
  };

  return (
    <div className="bg-ff-bg-secondary border border-ff-terminal-border rounded-lg p-4 hover:border-ff-purple/50 transition-colors card-glow">
      {/* Header: Name and Type */}
      <div className="mb-3">
        <h3 className="text-lg font-semibold text-ff-text-primary mb-1">
          {hotel.name}
        </h3>
        <span className="px-2 py-0.5 text-xs bg-ff-terminal rounded border border-ff-terminal-border text-ff-text-secondary">
          {hotel.type}
        </span>
      </div>

      {/* Rating and Price */}
      <div className="flex justify-between items-center mb-4">
        <StarRating rating={hotel.rating} />
        <div className="text-right">
          {hotel.price_range ? (
            <span className="text-xl font-bold gradient-text">
              {hotel.price_range}
            </span>
          ) : hotel.min_price ? (
            <span className="text-xl font-bold gradient-text">
              From {formatPrice(hotel.min_price)}
            </span>
          ) : (
            <span className="text-ff-text-dim">Price unavailable</span>
          )}
          <div className="text-ff-text-dim text-xs">per night</div>
        </div>
      </div>

      {/* Review Count */}
      {hotel.review_count != null && hotel.review_count > 0 && (
        <div className="text-ff-text-secondary text-sm mb-3">
          {hotel.review_count.toLocaleString()} reviews
        </div>
      )}

      {/* Highlights */}
      {hotel.highlights.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {hotel.highlights.slice(0, 4).map((highlight, idx) => (
            <span
              key={idx}
              className="px-2 py-0.5 text-xs bg-ff-purple/20 rounded border border-ff-purple/30 text-ff-purple"
            >
              {highlight}
            </span>
          ))}
        </div>
      )}

      {/* View Deal Button */}
      {hotel.url && (
        <button
          onClick={handleViewDeal}
          className="w-full py-2 px-4 bg-gradient-horizontal rounded-lg font-medium text-white hover:opacity-90 transition-opacity"
        >
          View Deal
        </button>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

interface TripHotelCardProps {
  hotel: TripHotel;
  nights?: number;
}

/**
 * Compact hotel card for trip search results.
 */
export function TripHotelCard({ hotel, nights = 1 }: TripHotelCardProps) {
  return (
    <div className="bg-ff-bg-secondary border border-ff-terminal-border rounded-lg p-3">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h4 className="font-medium text-ff-text-primary">{hotel.name}</h4>
          <span className="text-xs text-ff-text-secondary">{hotel.type}</span>
        </div>
        {hotel.rating != null && (
          <div className="text-ff-warning text-sm">
            ★ {hotel.rating.toFixed(1)}
          </div>
        )}
      </div>
      {hotel.price_per_night != null && (
        <div className="text-right">
          <span className="text-lg font-bold gradient-text">
            {formatPrice(hotel.price_per_night)}
          </span>
          <span className="text-ff-text-dim text-xs">/night</span>
          {nights > 1 && (
            <div className="text-ff-text-secondary text-xs">
              {formatPrice(hotel.price_per_night * nights)} total ({nights} nights)
            </div>
          )}
        </div>
      )}
    </div>
  );
}
