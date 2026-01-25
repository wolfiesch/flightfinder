import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS, SPRINGS } from "../styles/colors";

interface CodeBlockProps {
  code: string;
  language?: string;
  entranceDelay?: number;
  showCopyButton?: boolean;
  highlighted?: boolean;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = "bash",
  entranceDelay = 0,
  showCopyButton = false,
  highlighted = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entranceProgress = spring({
    frame: frame - entranceDelay,
    fps,
    config: SPRINGS.snappy,
  });

  const scale = interpolate(entranceProgress, [0, 1], [0.95, 1]);
  const opacity = interpolate(entranceProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Glow animation for highlighted
  const glowIntensity = highlighted
    ? 0.3 + Math.sin(frame * 0.08) * 0.15
    : 0;

  return (
    <div
      style={{
        backgroundColor: COLORS.terminal,
        border: `2px solid ${highlighted ? COLORS.accent : COLORS.terminalBorder}`,
        borderRadius: "12px",
        padding: "20px 24px",
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: "20px",
        color: COLORS.textPrimary,
        transform: `scale(${scale})`,
        opacity,
        boxShadow: highlighted
          ? `0 0 30px rgba(0, 212, 255, ${glowIntensity})`
          : "0 4px 20px rgba(0, 0, 0, 0.3)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "16px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        {/* Shell prompt */}
        <span style={{ color: COLORS.success }}>$</span>
        <span>{code}</span>
      </div>

      {/* Copy button */}
      {showCopyButton && (
        <div
          style={{
            padding: "8px 12px",
            backgroundColor: COLORS.terminalBorder,
            borderRadius: "6px",
            fontSize: "12px",
            color: COLORS.textSecondary,
          }}
        >
          Copy
        </div>
      )}
    </div>
  );
};
