import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS, SPRINGS } from "../styles/colors";
import { GradientText } from "../components/GradientText";
import { GradientGlow } from "../components/GradientGlow";

/**
 * RevealScene - 60 frames (2 seconds)
 * Logo reveal with animated multi-color glow
 *
 * Timeline:
 * - Frame 0-20: Logo entrance with glow
 * - Frame 20-40: "FlightFinder" text entrance
 * - Frame 40-60: Badge pulse
 */
export const RevealScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Logo entrance
  const logoProgress = spring({
    frame,
    fps,
    config: SPRINGS.premium,
  });

  const logoOpacity = interpolate(logoProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const logoScale = interpolate(logoProgress, [0, 1], [0.8, 1]);

  // Title entrance
  const titleProgress = spring({
    frame: frame - 15,
    fps,
    config: SPRINGS.smooth,
  });

  const titleOpacity = interpolate(titleProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Badge entrance with bounce
  const badgeProgress = spring({
    frame: frame - 30,
    fps,
    config: SPRINGS.bouncy,
  });

  const badgeOpacity = interpolate(badgeProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const badgeScale = interpolate(badgeProgress, [0, 1], [0.5, 1]);

  // Badge pulse animation
  const badgePulse = frame > 40
    ? interpolate(Math.sin((frame - 40) * 0.1) * 0.5 + 0.5, [0, 1], [1, 1.05])
    : 1;

  // Background glow intensity
  const glowIntensity = interpolate(
    Math.sin(frame * 0.05) * 0.5 + 0.5,
    [0, 1],
    [0.08, 0.15]
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "24px",
      }}
    >
      {/* Radial gradient glow background */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at center, rgba(0, 212, 255, ${glowIntensity}) 0%, transparent 50%)`,
          pointerEvents: "none",
        }}
      />

      {/* Logo with animated glow */}
      <GradientGlow
        intensity={1.5}
        animate={true}
        style={{
          opacity: logoOpacity,
          transform: `scale(${logoScale})`,
          borderRadius: "50%",
          padding: "20px",
        }}
      >
        <div
          style={{
            width: "100px",
            height: "100px",
            borderRadius: "50%",
            background: `linear-gradient(135deg, ${COLORS.cyan}, ${COLORS.purple})`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "48px",
            fontWeight: 800,
            fontFamily: "Inter, -apple-system, sans-serif",
            color: COLORS.bg,
          }}
        >
          FF
        </div>
      </GradientGlow>

      {/* FlightFinder title */}
      <div style={{ opacity: titleOpacity }}>
        <GradientText fontSize={56} fontWeight={700} animate={true}>
          FlightFinder
        </GradientText>
      </div>

      {/* Zero API Keys badge */}
      <div
        style={{
          opacity: badgeOpacity,
          transform: `scale(${badgeScale * badgePulse})`,
          marginTop: "16px",
        }}
      >
        <div
          style={{
            padding: "12px 28px",
            borderRadius: "24px",
            background: `linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(168, 85, 247, 0.15))`,
            border: `1px solid rgba(0, 212, 255, 0.3)`,
            fontFamily: "Inter, -apple-system, sans-serif",
            fontSize: "18px",
            fontWeight: 600,
            color: COLORS.cyan,
            letterSpacing: "0.5px",
          }}
        >
          Zero API Keys
        </div>
      </div>
    </AbsoluteFill>
  );
};
