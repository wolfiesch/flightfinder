import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS, SPRINGS } from "../styles/colors";

export const SolutionRevealScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Logo entrance with bounce
  const logoProgress = spring({
    frame,
    fps,
    config: SPRINGS.bouncy,
  });

  const logoScale = interpolate(logoProgress, [0, 1], [0.3, 1]);
  const logoOpacity = interpolate(logoProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Text entrance (staggered after logo)
  const textProgress = spring({
    frame: frame - 20,
    fps,
    config: SPRINGS.smooth,
  });

  const textOpacity = interpolate(textProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const textY = interpolate(textProgress, [0, 1], [30, 0]);

  // Tagline badges entrance
  const badges = [
    { text: "Zero API Keys", delay: 45, color: COLORS.success },
    { text: "Real-time Prices", delay: 55, color: COLORS.accent },
    { text: "MCP Ready", delay: 65, color: COLORS.warning },
  ];

  // Glow pulse animation
  const glowIntensity = 0.3 + Math.sin(frame * 0.1) * 0.15;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "40px",
      }}
    >
      {/* Logo/Icon */}
      <div
        style={{
          width: "140px",
          height: "140px",
          borderRadius: "28px",
          backgroundColor: COLORS.terminal,
          border: `3px solid ${COLORS.accent}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "56px",
          fontFamily: "'JetBrains Mono', monospace",
          fontWeight: 700,
          color: COLORS.accent,
          transform: `scale(${logoScale})`,
          opacity: logoOpacity,
          boxShadow: `0 0 60px rgba(0, 212, 255, ${glowIntensity})`,
        }}
      >
        FF
      </div>

      {/* Product name */}
      <div
        style={{
          fontFamily: "Inter, sans-serif",
          fontSize: "72px",
          fontWeight: 800,
          color: COLORS.textPrimary,
          opacity: textOpacity,
          transform: `translateY(${textY}px)`,
          letterSpacing: "-2px",
        }}
      >
        Flight
        <span style={{ color: COLORS.accent }}>Finder</span>
      </div>

      {/* Tagline */}
      <div
        style={{
          fontFamily: "Inter, sans-serif",
          fontSize: "28px",
          color: COLORS.textSecondary,
          opacity: textOpacity,
          transform: `translateY(${textY}px)`,
        }}
      >
        Search flights and hotels without the hassle
      </div>

      {/* Feature badges */}
      <div
        style={{
          display: "flex",
          gap: "20px",
          marginTop: "20px",
        }}
      >
        {badges.map((badge, index) => {
          const badgeProgress = spring({
            frame: frame - badge.delay,
            fps,
            config: SPRINGS.snappy,
          });
          const badgeOpacity = interpolate(badgeProgress, [0, 1], [0, 1], {
            extrapolateRight: "clamp",
          });
          const badgeScale = interpolate(badgeProgress, [0, 1], [0.8, 1]);

          return (
            <div
              key={index}
              style={{
                padding: "12px 24px",
                backgroundColor: COLORS.terminal,
                border: `2px solid ${badge.color}`,
                borderRadius: "100px",
                fontFamily: "Inter, sans-serif",
                fontSize: "18px",
                fontWeight: 600,
                color: badge.color,
                opacity: badgeOpacity,
                transform: `scale(${badgeScale})`,
              }}
            >
              {badge.text}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
