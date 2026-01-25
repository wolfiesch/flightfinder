import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  Sequence,
} from "remotion";
import { COLORS, TERMINAL_FONT } from "../styles/colors";
import { TerminalPrompt } from "../components/TerminalPrompt";
import { ReceiptBox } from "../components/TerminalTable";

export const TripPlanningScene: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        padding: "60px 80px",
        display: "flex",
        flexDirection: "column",
        gap: "24px",
      }}
    >
      {/* Scene title - terminal style */}
      <div
        style={{
          fontFamily: TERMINAL_FONT,
          fontSize: "16px",
          fontWeight: 500,
          color: COLORS.textDim,
          opacity: interpolate(frame, [0, 20], [0, 1], {
            extrapolateRight: "clamp",
          }),
        }}
      >
        # Trip Planning
      </div>

      {/* Terminal-style prompts */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* User prompt */}
        <Sequence from={10} durationInFrames={240} layout="none">
          <TerminalPrompt
            message="Plan a 7-night trip to Tokyo with flights and hotels"
            isUser={true}
            entranceDelay={0}
          />
        </Sequence>

        {/* Claude response */}
        <Sequence from={45} durationInFrames={205} layout="none">
          <TerminalPrompt
            message="Building your complete trip package..."
            isUser={false}
            entranceDelay={0}
          />
        </Sequence>
      </div>

      {/* Trip receipt box */}
      <Sequence from={80} durationInFrames={170} layout="none">
        <div style={{ marginLeft: "24px" }}>
          <ReceiptBox
            title="7-NIGHT TOKYO TRIP"
            items={[
              {
                icon: "FLT:",
                label: "SFO → Tokyo (Round trip)",
                sublabel: "Multiple Airlines",
                value: "$489",
              },
              {
                icon: "HTL:",
                label: "Shinjuku Granbell Hotel",
                sublabel: "7 nights × $120/night",
                value: "$840",
              },
            ]}
            total={{
              label: "TOTAL",
              value: "$1,329",
            }}
            entranceDelay={0}
          />
        </div>
      </Sequence>

      {/* Savings callout - terminal style */}
      <Sequence from={200} durationInFrames={50} layout="none">
        <div
          style={{
            marginLeft: "24px",
            fontFamily: TERMINAL_FONT,
            fontSize: "16px",
            opacity: interpolate(
              frame - 200,
              [0, 20],
              [0, 1],
              { extrapolateRight: "clamp" }
            ),
          }}
        >
          <span style={{ color: COLORS.accent }}>{">>> "}</span>
          <span style={{ color: COLORS.textSecondary }}>
            Combined search saves hours of manual research
          </span>
        </div>
      </Sequence>
    </AbsoluteFill>
  );
};
