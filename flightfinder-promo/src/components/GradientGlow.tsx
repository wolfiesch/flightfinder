import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS } from "../styles/colors";

interface GradientGlowProps {
  children: React.ReactNode;
  intensity?: number;
  animate?: boolean;
  style?: React.CSSProperties;
}

/**
 * Wrapper component that adds animated multi-color glow to children
 * Uses layered box-shadows that shift colors based on frame
 */
export const GradientGlow: React.FC<GradientGlowProps> = ({
  children,
  intensity = 1,
  animate = true,
  style = {},
}) => {
  const frame = useCurrentFrame();

  // Breathing sine wave animation for glow intensity
  const breathingPhase = animate ? Math.sin(frame * 0.03) * 0.5 + 0.5 : 0.5;
  const pulseIntensity = interpolate(breathingPhase, [0, 1], [0.6, 1]) * intensity;

  // Shift color emphasis over time
  const colorPhase = animate ? (frame % 180) / 180 : 0;

  // Calculate individual color intensities based on phase
  const cyanIntensity = interpolate(
    Math.sin(colorPhase * Math.PI * 2),
    [-1, 1],
    [0.2, 0.4]
  ) * pulseIntensity;

  const purpleIntensity = interpolate(
    Math.sin((colorPhase + 0.33) * Math.PI * 2),
    [-1, 1],
    [0.15, 0.3]
  ) * pulseIntensity;

  const pinkIntensity = interpolate(
    Math.sin((colorPhase + 0.66) * Math.PI * 2),
    [-1, 1],
    [0.1, 0.2]
  ) * pulseIntensity;

  const boxShadow = `
    0 0 40px rgba(0, 212, 255, ${cyanIntensity}),
    0 0 80px rgba(168, 85, 247, ${purpleIntensity}),
    0 0 120px rgba(236, 72, 153, ${pinkIntensity})
  `;

  return (
    <div
      style={{
        boxShadow,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
