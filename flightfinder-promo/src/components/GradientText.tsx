import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { GRADIENTS, GLOWS, COLORS } from "../styles/colors";

interface GradientTextProps {
  children: React.ReactNode;
  fontSize?: number;
  fontWeight?: number;
  animate?: boolean;
  glow?: boolean;
  style?: React.CSSProperties;
}

/**
 * Premium gradient text component with animated gradient position
 * Uses CSS background-clip: text for the gradient effect
 */
export const GradientText: React.FC<GradientTextProps> = ({
  children,
  fontSize = 48,
  fontWeight = 700,
  animate = true,
  glow = true,
  style = {},
}) => {
  const frame = useCurrentFrame();

  // Animate gradient position for shimmer effect
  const gradientPosition = animate
    ? interpolate(frame, [0, 120], [0, 100], {
        extrapolateRight: "clamp",
      })
    : 50;

  // Subtle glow pulse
  const glowOpacity = animate
    ? interpolate(
        Math.sin(frame * 0.05) * 0.5 + 0.5,
        [0, 1],
        [0.3, 0.6]
      )
    : 0.5;

  return (
    <span
      style={{
        fontFamily: "Inter, -apple-system, sans-serif",
        fontSize,
        fontWeight,
        background: `linear-gradient(90deg,
          ${COLORS.cyan} ${gradientPosition - 50}%,
          ${COLORS.purple} ${gradientPosition}%,
          ${COLORS.pink} ${gradientPosition + 50}%
        )`,
        backgroundClip: "text",
        WebkitBackgroundClip: "text",
        WebkitTextFillColor: "transparent",
        textShadow: glow
          ? `0 0 40px rgba(0, 212, 255, ${glowOpacity}), 0 0 80px rgba(168, 85, 247, ${glowOpacity * 0.5})`
          : "none",
        ...style,
      }}
    >
      {children}
    </span>
  );
};
