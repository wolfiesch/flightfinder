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

/**
 * HookScene - 90 frames (3 seconds)
 * Capability-focused hook to grab attention in first 3 seconds
 *
 * Timeline:
 * - Frame 0-15: Black (hold)
 * - Frame 15-45: Line 1: "Ever wanted to give Claude"
 * - Frame 30-60: Line 2: "the ability to search flights?"
 * - Frame 55-90: Subtext: "Now you can. Plug & play."
 */
export const HookScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Line 1 entrance: "Ever wanted to give Claude" (starts at frame 15)
  const line1Progress = spring({
    frame: frame - 15,
    fps,
    config: SPRINGS.premium,
  });

  const line1Opacity = interpolate(line1Progress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const line1Y = interpolate(line1Progress, [0, 1], [30, 0]);
  const line1Scale = interpolate(line1Progress, [0, 1], [0.95, 1]);

  // Line 2 entrance: "the ability to search flights?" (starts at frame 30)
  const line2Progress = spring({
    frame: frame - 30,
    fps,
    config: SPRINGS.premium,
  });

  const line2Opacity = interpolate(line2Progress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const line2Y = interpolate(line2Progress, [0, 1], [20, 0]);

  // Subtext entrance: "Now you can. Plug & play." (starts at frame 55)
  const subtextProgress = spring({
    frame: frame - 55,
    fps,
    config: SPRINGS.smooth,
  });

  const subtextOpacity = interpolate(subtextProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Radial glow background pulse
  const glowIntensity = interpolate(
    Math.sin(frame * 0.04) * 0.5 + 0.5,
    [0, 1],
    [0.1, 0.2]
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "80px",
      }}
    >
      {/* Radial gradient glow background */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at center, rgba(168, 85, 247, ${glowIntensity}) 0%, transparent 60%)`,
          pointerEvents: "none",
        }}
      />

      {/* Main question - two lines */}
      <div
        style={{
          textAlign: "center",
          display: "flex",
          flexDirection: "column",
          gap: "8px",
        }}
      >
        {/* Line 1: "Ever wanted to give Claude" */}
        <div
          style={{
            opacity: line1Opacity,
            transform: `translateY(${line1Y}px) scale(${line1Scale})`,
          }}
        >
          <GradientText fontSize={64} fontWeight={800} animate={frame > 15}>
            Ever wanted to give Claude
          </GradientText>
        </div>

        {/* Line 2: "the ability to search flights?" */}
        <div
          style={{
            opacity: line2Opacity,
            transform: `translateY(${line2Y}px)`,
          }}
        >
          <GradientText fontSize={64} fontWeight={800} animate={frame > 30}>
            the ability to search flights?
          </GradientText>
        </div>
      </div>

      {/* Subtext - positive affirmation */}
      <div
        style={{
          fontFamily: "Inter, -apple-system, sans-serif",
          fontSize: "32px",
          fontWeight: 500,
          color: COLORS.textSecondary,
          textAlign: "center",
          marginTop: "40px",
          opacity: subtextOpacity,
          lineHeight: 1.5,
        }}
      >
        Now you can. Plug & play.
      </div>
    </AbsoluteFill>
  );
};
