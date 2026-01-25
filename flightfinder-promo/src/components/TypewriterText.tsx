import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS, CHAR_FRAMES } from "../styles/colors";

interface TypewriterTextProps {
  text: string;
  startFrame?: number;
  charFrames?: number;
  showCursor?: boolean;
  cursorChar?: string;
  color?: string;
  fontSize?: number;
  fontWeight?: number;
  prefix?: string;
  prefixColor?: string;
}

export const TypewriterText: React.FC<TypewriterTextProps> = ({
  text,
  startFrame = 0,
  charFrames = CHAR_FRAMES,
  showCursor = true,
  cursorChar = "█",
  color = COLORS.textPrimary,
  fontSize = 18,
  fontWeight = 400,
  prefix = "",
  prefixColor = COLORS.success,
}) => {
  const frame = useCurrentFrame();
  const localFrame = Math.max(0, frame - startFrame);

  // Calculate how many characters to show
  const charsToShow = Math.floor(localFrame / charFrames);
  const visibleText = text.slice(0, charsToShow);
  const isComplete = charsToShow >= text.length;

  // Cursor blink (16 frame cycle)
  const cursorOpacity =
    showCursor && !isComplete
      ? interpolate(
          localFrame % 16,
          [0, 8, 16],
          [1, 0, 1],
          { extrapolateRight: "clamp" }
        )
      : 0;

  return (
    <span
      style={{
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: `${fontSize}px`,
        fontWeight,
        whiteSpace: "pre",
      }}
    >
      {prefix && (
        <span style={{ color: prefixColor }}>{prefix}</span>
      )}
      <span style={{ color }}>{visibleText}</span>
      <span style={{ color: COLORS.accent, opacity: cursorOpacity }}>
        {cursorChar}
      </span>
    </span>
  );
};

// Hook version for more control
export const useTypewriter = (
  text: string,
  startFrame = 0,
  charFrames = CHAR_FRAMES
): { text: string; isComplete: boolean; progress: number } => {
  const frame = useCurrentFrame();
  const localFrame = Math.max(0, frame - startFrame);
  const charsToShow = Math.floor(localFrame / charFrames);

  return {
    text: text.slice(0, charsToShow),
    isComplete: charsToShow >= text.length,
    progress: Math.min(1, charsToShow / text.length),
  };
};
