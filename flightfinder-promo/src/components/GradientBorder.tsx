import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS, GRADIENTS } from "../styles/colors";

interface GradientBorderProps {
  children: React.ReactNode;
  width?: number;
  borderRadius?: number;
  animate?: boolean;
  style?: React.CSSProperties;
}

/**
 * Container with animated gradient border
 * Uses pseudo-element technique with gradient background and solid inner content
 */
export const GradientBorder: React.FC<GradientBorderProps> = ({
  children,
  width = 2,
  borderRadius = 8,
  animate = true,
  style = {},
}) => {
  const frame = useCurrentFrame();

  // Animate gradient rotation for flowing effect
  const rotation = animate
    ? interpolate(frame, [0, 180], [0, 360], {
        extrapolateRight: "extend",
      })
    : 135;

  return (
    <div
      style={{
        position: "relative",
        padding: width,
        borderRadius,
        background: `linear-gradient(${rotation}deg, ${COLORS.cyan}, ${COLORS.purple}, ${COLORS.pink})`,
        ...style,
      }}
    >
      <div
        style={{
          background: COLORS.terminal,
          borderRadius: Math.max(0, borderRadius - width),
          height: "100%",
          width: "100%",
        }}
      >
        {children}
      </div>
    </div>
  );
};
