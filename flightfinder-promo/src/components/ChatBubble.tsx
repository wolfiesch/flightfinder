import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS, SPRINGS } from "../styles/colors";

interface ChatBubbleProps {
  message: string;
  isAI?: boolean;
  entranceDelay?: number;
  showAvatar?: boolean;
  avatarText?: string;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({
  message,
  isAI = true,
  entranceDelay = 0,
  showAvatar = true,
  avatarText,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entranceProgress = spring({
    frame: frame - entranceDelay,
    fps,
    config: SPRINGS.snappy,
  });

  const scale = interpolate(entranceProgress, [0, 1], [0.8, 1]);
  const opacity = interpolate(entranceProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const translateX = interpolate(
    entranceProgress,
    [0, 1],
    [isAI ? -30 : 30, 0]
  );

  const bgColor = isAI ? COLORS.chatAI : COLORS.chatUser;
  const avatar = avatarText || (isAI ? "AI" : ">");

  return (
    <div
      style={{
        display: "flex",
        flexDirection: isAI ? "row" : "row-reverse",
        alignItems: "flex-start",
        gap: "12px",
        transform: `scale(${scale}) translateX(${translateX}px)`,
        opacity,
      }}
    >
      {/* Avatar */}
      {showAvatar && (
        <div
          style={{
            width: "44px",
            height: "44px",
            borderRadius: "50%",
            backgroundColor: bgColor,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "16px",
            fontFamily: "'JetBrains Mono', monospace",
            fontWeight: 600,
            color: COLORS.textPrimary,
            flexShrink: 0,
          }}
        >
          {avatar}
        </div>
      )}

      {/* Message bubble */}
      <div
        style={{
          backgroundColor: bgColor,
          padding: "16px 20px",
          borderRadius: isAI ? "4px 20px 20px 20px" : "20px 4px 20px 20px",
          maxWidth: "600px",
          color: COLORS.textPrimary,
          fontFamily: "Inter, sans-serif",
          fontSize: "18px",
          lineHeight: 1.5,
        }}
      >
        {message}
      </div>
    </div>
  );
};
