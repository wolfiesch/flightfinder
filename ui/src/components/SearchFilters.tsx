import { useState } from 'react';

// ─────────────────────────────────────────────────────────────────────────────
// Sort Options
// ─────────────────────────────────────────────────────────────────────────────

export type FlightSortOption = 'price' | 'duration' | 'departure';
export type HotelSortOption = 'price' | 'rating' | 'reviews';

interface SortSelectProps<T extends string> {
  value: T;
  onChange: (value: T) => void;
  options: { value: T; label: string }[];
}

export function SortSelect<T extends string>({ value, onChange, options }: SortSelectProps<T>) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-ff-text-secondary text-sm">Sort by:</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as T)}
        className="bg-ff-terminal border border-ff-terminal-border rounded px-3 py-1.5 text-ff-text-primary text-sm focus:outline-none focus:border-ff-purple"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Flight Filters
// ─────────────────────────────────────────────────────────────────────────────

interface FlightFiltersProps {
  maxStops: number | null;
  onMaxStopsChange: (value: number | null) => void;
  sortBy: FlightSortOption;
  onSortChange: (value: FlightSortOption) => void;
}

export function FlightFilters({
  maxStops,
  onMaxStopsChange,
  sortBy,
  onSortChange,
}: FlightFiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 mb-4">
      {/* Max Stops Toggle */}
      <div className="flex items-center gap-2">
        <label className="text-ff-text-secondary text-sm">Max stops:</label>
        <div className="flex gap-1">
          {[null, 0, 1, 2].map((stops) => (
            <button
              key={stops ?? 'any'}
              onClick={() => onMaxStopsChange(stops)}
              className={`px-3 py-1 text-sm rounded border transition-colors ${
                maxStops === stops
                  ? 'bg-ff-purple border-ff-purple text-white'
                  : 'border-ff-terminal-border text-ff-text-secondary hover:border-ff-purple/50'
              }`}
            >
              {stops === null ? 'Any' : stops === 0 ? 'Direct' : stops}
            </button>
          ))}
        </div>
      </div>

      {/* Sort Select */}
      <SortSelect
        value={sortBy}
        onChange={onSortChange}
        options={[
          { value: 'price', label: 'Price (Low to High)' },
          { value: 'duration', label: 'Duration (Shortest)' },
          { value: 'departure', label: 'Departure (Earliest)' },
        ]}
      />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Hotel Filters
// ─────────────────────────────────────────────────────────────────────────────

interface HotelFiltersProps {
  minRating: number | null;
  onMinRatingChange: (value: number | null) => void;
  sortBy: HotelSortOption;
  onSortChange: (value: HotelSortOption) => void;
}

export function HotelFilters({
  minRating,
  onMinRatingChange,
  sortBy,
  onSortChange,
}: HotelFiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 mb-4">
      {/* Min Rating Toggle */}
      <div className="flex items-center gap-2">
        <label className="text-ff-text-secondary text-sm">Min rating:</label>
        <div className="flex gap-1">
          {[null, 3, 3.5, 4, 4.5].map((rating) => (
            <button
              key={rating ?? 'any'}
              onClick={() => onMinRatingChange(rating)}
              className={`px-3 py-1 text-sm rounded border transition-colors ${
                minRating === rating
                  ? 'bg-ff-purple border-ff-purple text-white'
                  : 'border-ff-terminal-border text-ff-text-secondary hover:border-ff-purple/50'
              }`}
            >
              {rating === null ? 'Any' : `${rating}+`}
            </button>
          ))}
        </div>
      </div>

      {/* Sort Select */}
      <SortSelect
        value={sortBy}
        onChange={onSortChange}
        options={[
          { value: 'price', label: 'Price (Low to High)' },
          { value: 'rating', label: 'Rating (Highest)' },
          { value: 'reviews', label: 'Reviews (Most)' },
        ]}
      />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Price Range Slider (future enhancement)
// ─────────────────────────────────────────────────────────────────────────────

interface PriceRangeProps {
  min: number;
  max: number;
  value: [number, number];
  onChange: (value: [number, number]) => void;
}

export function PriceRange({ min, max, value, onChange }: PriceRangeProps) {
  const [localValue, setLocalValue] = useState(value);

  const handleMinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newMin = Number(e.target.value);
    const newValue: [number, number] = [newMin, Math.max(newMin, localValue[1])];
    setLocalValue(newValue);
  };

  const handleMaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newMax = Number(e.target.value);
    const newValue: [number, number] = [Math.min(localValue[0], newMax), newMax];
    setLocalValue(newValue);
  };

  const handleMouseUp = () => {
    onChange(localValue);
  };

  return (
    <div className="flex items-center gap-4">
      <label className="text-ff-text-secondary text-sm">Price:</label>
      <div className="flex items-center gap-2">
        <span className="text-ff-text-dim text-sm">${localValue[0]}</span>
        <input
          type="range"
          min={min}
          max={max}
          value={localValue[0]}
          onChange={handleMinChange}
          onMouseUp={handleMouseUp}
          onTouchEnd={handleMouseUp}
          className="w-24"
        />
        <span className="text-ff-text-dim">-</span>
        <input
          type="range"
          min={min}
          max={max}
          value={localValue[1]}
          onChange={handleMaxChange}
          onMouseUp={handleMouseUp}
          onTouchEnd={handleMouseUp}
          className="w-24"
        />
        <span className="text-ff-text-dim text-sm">${localValue[1]}</span>
      </div>
    </div>
  );
}
