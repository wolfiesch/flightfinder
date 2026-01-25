import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS, TERMINAL_FONT, SPRINGS } from "../styles/colors";

interface TerminalPromptProps {
  message: string;
  isUser?: boolean;
  entranceDelay?: number;
  showCursor?: boolean;
  typewriter?: boolean;
}

export const TerminalPrompt: React.FC<TerminalPromptProps> = ({
  message,
  isUser = false,
  entranceDelay = 0,
  showCursor = false,
  typewriter = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance animation
  const entranceProgress = spring({
    frame: frame - entranceDelay,
    fps,
    config: SPRINGS.snappy,
  });

  const opacity = interpolate(entranceProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const translateX = interpolate(entranceProgress, [0, 1], [-20, 0]);

  // Typewriter effect
  const adjustedFrame = Math.max(0, frame - entranceDelay);
  const charsPerFrame = 0.8; // Characters revealed per frame
  const visibleChars = typewriter
    ? Math.min(Math.floor(adjustedFrame * charsPerFrame), message.length)
    : message.length;
  const displayMessage = message.slice(0, visibleChars);

  // Blinking cursor (blinks every ~15 frames)
  const cursorVisible = showCursor && Math.floor(frame / 15) % 2 === 0;
  const showCursorNow = typewriter ? visibleChars < message.length || cursorVisible : cursorVisible;

  // Prompt symbol and color
  const promptSymbol = isUser ? ">" : "*";
  const promptColor = isUser ? COLORS.promptUser : COLORS.promptClaude;

  return (
    <div
      style={{
        display: "flex",
        gap: "12px",
        fontFamily: TERMINAL_FONT,
        fontSize: "18px",
        lineHeight: 1.6,
        transform: `translateX(${translateX}px)`,
        opacity,
      }}
    >
      {/* Prompt symbol */}
      <span
        style={{
          color: promptColor,
          fontWeight: 600,
          flexShrink: 0,
        }}
      >
        {promptSymbol}
      </span>

      {/* Message text */}
      <span style={{ color: COLORS.textPrimary }}>
        {displayMessage}
        {showCursorNow && (
          <span
            style={{
              display: "inline-block",
              width: "10px",
              height: "20px",
              backgroundColor: COLORS.textPrimary,
              marginLeft: "2px",
              verticalAlign: "text-bottom",
            }}
          />
        )}
      </span>
    </div>
  );
};
