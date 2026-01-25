import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS, TERMINAL_FONT, SPRINGS } from "../styles/colors";

interface TerminalProps {
  children: React.ReactNode;
  title?: string;
  width?: number | string;
  height?: number | string;
  animateEntrance?: boolean;
  entranceDelay?: number;
  glowColor?: "cyan" | "purple" | "multi";
  glowIntensity?: number;
  gradientBorder?: boolean;
}

export const Terminal: React.FC<TerminalProps> = ({
  children,
  title = "terminal",
  width = 900,
  height = 500,
  animateEntrance = true,
  entranceDelay = 0,
  glowColor,
  glowIntensity = 1,
  gradientBorder = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance animation
  const entranceProgress = animateEntrance
    ? spring({
        frame: frame - entranceDelay,
        fps,
        config: SPRINGS.smooth,
      })
    : 1;

  const scale = interpolate(entranceProgress, [0, 1], [0.95, 1]);
  const opacity = interpolate(entranceProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(entranceProgress, [0, 1], [20, 0]);

  // Glow color mapping
  const getGlowShadow = () => {
    if (!glowColor) return "none";
    const intensity = glowIntensity;
    switch (glowColor) {
      case "cyan":
        return `0 0 ${40 * intensity}px rgba(0, 212, 255, ${0.3 * intensity})`;
      case "purple":
        return `0 0 ${40 * intensity}px rgba(168, 85, 247, ${0.3 * intensity})`;
      case "multi":
        return `0 0 ${30 * intensity}px rgba(0, 212, 255, ${0.25 * intensity}), 0 0 ${60 * intensity}px rgba(168, 85, 247, ${0.2 * intensity}), 0 0 ${90 * intensity}px rgba(236, 72, 153, ${0.1 * intensity})`;
      default:
        return "none";
    }
  };

  // Gradient border style
  const borderStyle = gradientBorder
    ? {
        border: "none",
        background: `linear-gradient(${COLORS.terminal}, ${COLORS.terminal}) padding-box, linear-gradient(135deg, ${COLORS.cyan}, ${COLORS.purple}, ${COLORS.pink}) border-box`,
        borderWidth: "1px",
        borderStyle: "solid",
        borderColor: "transparent",
      }
    : {
        border: `1px solid ${COLORS.terminalBorder}`,
      };

  return (
    <div
      style={{
        width: typeof width === "number" ? `${width}px` : width,
        height: typeof height === "number" ? `${height}px` : height,
        backgroundColor: COLORS.terminal,
        ...borderStyle,
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        transform: `scale(${scale}) translateY(${translateY}px)`,
        opacity,
        boxShadow: getGlowShadow(),
      }}
    >
      {/* Minimal title bar - flat, no traffic lights */}
      <div
        style={{
          height: "32px",
          backgroundColor: COLORS.bg,
          borderBottom: `1px solid ${COLORS.terminalBorder}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "0 16px",
        }}
      >
        {/* Title - terminal style */}
        <div
          style={{
            color: COLORS.textDim,
            fontSize: "12px",
            fontFamily: TERMINAL_FONT,
            letterSpacing: "0.5px",
          }}
        >
          {title}
        </div>
      </div>

      {/* Content area */}
      <div
        style={{
          flex: 1,
          padding: "20px",
          fontFamily: TERMINAL_FONT,
          fontSize: "16px",
          lineHeight: 1.6,
          color: COLORS.textPrimary,
          overflow: "hidden",
        }}
      >
        {children}
      </div>
    </div>
  );
};
