import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS, SPRINGS, CHAR_FRAMES } from "../styles/colors";
import { Terminal } from "../components/Terminal";
import { GradientGlow } from "../components/GradientGlow";

/**
 * InstallationScene - 150 frames (5 seconds)
 * Fast, snappy installation demo
 *
 * Timeline:
 * - Frame 0-15: Terminal entrance
 * - Frame 15-60: Typewriter command (2x faster with CHAR_FRAMES=1)
 * - Frame 60-100: All success messages appear together
 * - Frame 100-150: Glow pulse on [DONE]
 */
export const InstallationScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const COMMAND = "npx skills install flightfinder";

  // Terminal entrance
  const terminalProgress = spring({
    frame,
    fps,
    config: SPRINGS.premium,
  });

  // Typewriter effect - 2x faster
  const typewriterStart = 15;
  const localTypeFrame = Math.max(0, frame - typewriterStart);
  const charsToShow = Math.floor(localTypeFrame / CHAR_FRAMES);
  const visibleCommand = COMMAND.slice(0, charsToShow);
  const isTypingComplete = charsToShow >= COMMAND.length;

  // Cursor blink
  const cursorOpacity = !isTypingComplete
    ? interpolate(localTypeFrame % 12, [0, 6, 12], [1, 0, 1], {
        extrapolateRight: "clamp",
      })
    : 0;

  // Success messages - appear together after typing
  const successDelay = typewriterStart + COMMAND.length * CHAR_FRAMES + 15;
  const showSuccess = frame > successDelay;

  const successProgress = spring({
    frame: frame - successDelay,
    fps,
    config: SPRINGS.snappy,
  });

  const successOpacity = interpolate(successProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Done message pulse
  const doneDelay = successDelay + 20;
  const showDone = frame > doneDelay;

  const doneProgress = spring({
    frame: frame - doneDelay,
    fps,
    config: SPRINGS.bouncy,
  });

  const doneScale = interpolate(doneProgress, [0, 1], [0.8, 1]);
  const doneOpacity = interpolate(doneProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Glow intensity based on frame
  const glowIntensity = showDone
    ? interpolate(Math.sin((frame - doneDelay) * 0.1) * 0.5 + 0.5, [0, 1], [0.8, 1.2])
    : 0.5;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "60px",
      }}
    >
      {/* Section title */}
      <div
        style={{
          fontFamily: "Inter, -apple-system, sans-serif",
          fontSize: "24px",
          fontWeight: 600,
          color: COLORS.textSecondary,
          marginBottom: "40px",
          opacity: interpolate(terminalProgress, [0, 1], [0, 1]),
        }}
      >
        One command. That's it.
      </div>

      <GradientGlow
        intensity={glowIntensity}
        animate={showDone}
        style={{
          borderRadius: "8px",
        }}
      >
        <Terminal
          title="Terminal"
          width={900}
          height={320}
          animateEntrance={true}
          entranceDelay={0}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {/* Command line */}
            <div style={{ display: "flex", alignItems: "center" }}>
              <span style={{ color: COLORS.success, marginRight: "12px" }}>$</span>
              <span style={{ color: COLORS.textPrimary }}>{visibleCommand}</span>
              <span style={{ color: COLORS.cyan, opacity: cursorOpacity }}>█</span>
            </div>

            {/* Success output - all appear together */}
            {showSuccess && (
              <div
                style={{
                  opacity: successOpacity,
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                }}
              >
                <div style={{ color: COLORS.textSecondary }}>
                  <span style={{ color: COLORS.success }}>[OK]</span> Downloaded flightfinder@1.0.0
                </div>
                <div style={{ color: COLORS.textSecondary }}>
                  <span style={{ color: COLORS.success }}>[OK]</span> Verified MCP server
                </div>
                <div style={{ color: COLORS.textSecondary }}>
                  <span style={{ color: COLORS.success }}>[OK]</span> Added to Claude Code
                </div>
              </div>
            )}

            {/* Done message with glow */}
            {showDone && (
              <div
                style={{
                  color: COLORS.cyan,
                  marginTop: "8px",
                  fontSize: "18px",
                  fontWeight: 600,
                  opacity: doneOpacity,
                  transform: `scale(${doneScale})`,
                  transformOrigin: "left",
                  textShadow: `0 0 20px rgba(0, 212, 255, 0.5)`,
                }}
              >
                [DONE] FlightFinder ready!
              </div>
            )}
          </div>
        </Terminal>
      </GradientGlow>
    </AbsoluteFill>
  );
};
