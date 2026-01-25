import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS, SPRINGS } from "../styles/colors";

interface FlightResultProps {
  from: string;
  to: string;
  price: number;
  airline?: string;
  duration?: string;
  isHighlighted?: boolean;
  entranceDelay?: number;
}

export const FlightResultCard: React.FC<FlightResultProps> = ({
  from,
  to,
  price,
  airline = "Multiple Airlines",
  duration = "12h 30m",
  isHighlighted = false,
  entranceDelay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entranceProgress = spring({
    frame: frame - entranceDelay,
    fps,
    config: isHighlighted ? SPRINGS.bouncy : SPRINGS.snappy,
  });

  const scale = interpolate(entranceProgress, [0, 1], [0.8, 1]);
  const opacity = interpolate(entranceProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(entranceProgress, [0, 1], [20, 0]);

  // Pulse animation for highlighted card
  const pulseScale = isHighlighted
    ? 1 + Math.sin(frame * 0.1) * 0.02
    : 1;

  return (
    <div
      style={{
        backgroundColor: isHighlighted ? COLORS.terminalBorder : COLORS.terminal,
        border: `2px solid ${isHighlighted ? COLORS.accent : COLORS.terminalBorder}`,
        borderRadius: "12px",
        padding: "20px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        transform: `scale(${scale * pulseScale}) translateY(${translateY}px)`,
        opacity,
        boxShadow: isHighlighted ? COLORS.accent + "40 0 0 20px" : "none",
      }}
    >
      {/* Route info */}
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            fontFamily: "Inter, sans-serif",
            fontSize: "20px",
            fontWeight: 600,
            color: COLORS.textPrimary,
          }}
        >
          <span>{from}</span>
          <span style={{ color: COLORS.accent }}>→</span>
          <span>{to}</span>
        </div>
        <div
          style={{
            fontFamily: "Inter, sans-serif",
            fontSize: "14px",
            color: COLORS.textSecondary,
          }}
        >
          {airline} • {duration}
        </div>
      </div>

      {/* Price */}
      <div
        style={{
          fontFamily: "Inter, sans-serif",
          fontSize: isHighlighted ? "32px" : "28px",
          fontWeight: 700,
          color: isHighlighted ? COLORS.price : COLORS.textPrimary,
        }}
      >
        ${price}
      </div>
    </div>
  );
};

interface HotelResultProps {
  name: string;
  stars: number;
  pricePerNight: number;
  location?: string;
  entranceDelay?: number;
}

export const HotelResultCard: React.FC<HotelResultProps> = ({
  name,
  stars,
  pricePerNight,
  location = "",
  entranceDelay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entranceProgress = spring({
    frame: frame - entranceDelay,
    fps,
    config: SPRINGS.snappy,
  });

  const scale = interpolate(entranceProgress, [0, 1], [0.8, 1]);
  const opacity = interpolate(entranceProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        backgroundColor: COLORS.terminal,
        border: `1px solid ${COLORS.terminalBorder}`,
        borderRadius: "12px",
        padding: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        transform: `scale(${scale})`,
        opacity,
        minWidth: "200px",
      }}
    >
      {/* Hotel name */}
      <div
        style={{
          fontFamily: "Inter, sans-serif",
          fontSize: "16px",
          fontWeight: 600,
          color: COLORS.textPrimary,
        }}
      >
        {name}
      </div>

      {/* Stars */}
      <div style={{ display: "flex", gap: "2px" }}>
        {Array.from({ length: 5 }, (_, i) => (
          <span
            key={i}
            style={{
              color: i < stars ? COLORS.warning : COLORS.textDim,
              fontSize: "14px",
            }}
          >
            ★
          </span>
        ))}
      </div>

      {/* Location */}
      {location && (
        <div
          style={{
            fontFamily: "Inter, sans-serif",
            fontSize: "12px",
            color: COLORS.textSecondary,
          }}
        >
          {location}
        </div>
      )}

      {/* Price */}
      <div
        style={{
          fontFamily: "Inter, sans-serif",
          fontSize: "20px",
          fontWeight: 700,
          color: COLORS.accent,
          marginTop: "auto",
        }}
      >
        ${pricePerNight}
        <span
          style={{
            fontSize: "12px",
            fontWeight: 400,
            color: COLORS.textSecondary,
          }}
        >
          /night
        </span>
      </div>
    </div>
  );
};
