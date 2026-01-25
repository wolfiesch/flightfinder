import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  Sequence,
} from "remotion";
import { COLORS, TERMINAL_FONT, SPRINGS } from "../styles/colors";
import { TerminalPrompt } from "../components/TerminalPrompt";
import { TerminalTable } from "../components/TerminalTable";

export const HotelSearchScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Hotel data for the terminal table
  const columns = [
    { header: "HOTEL", key: "name", width: 20, align: "left" as const },
    { header: "LOCATION", key: "location", width: 12, align: "left" as const },
    { header: "STARS", key: "stars", width: 7, align: "center" as const },
    { header: "PRICE", key: "price", width: 10, align: "right" as const },
  ];

  const rows = [
    { name: "Park Hyatt Tokyo", location: "Shinjuku", stars: "★★★★★", price: "$400/nt" },
    { name: "Shinjuku Granbell", location: "Shinjuku", stars: "★★★★", price: "$120/nt" },
    { name: "Shibuya Excel", location: "Shibuya", stars: "★★★★", price: "$150/nt" },
    { name: "Tokyo Bay Hilton", location: "Odaiba", stars: "★★★★★", price: "$280/nt" },
    { name: "Capsule Hotel 9h", location: "Shinjuku", stars: "★★★", price: "$45/nt" },
    { name: "APA Hotel", location: "Akihabara", stars: "★★★", price: "$65/nt" },
  ];

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
        # Hotel Search
      </div>

      {/* Terminal-style prompts */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* User prompt */}
        <Sequence from={10} durationInFrames={290} layout="none">
          <TerminalPrompt
            message="What hotels are available in Tokyo?"
            isUser={true}
            entranceDelay={0}
          />
        </Sequence>

        {/* Claude response */}
        <Sequence from={40} durationInFrames={260} layout="none">
          <TerminalPrompt
            message="Found hotels across 30+ cities. Results for Tokyo:"
            isUser={false}
            entranceDelay={0}
          />
        </Sequence>
      </div>

      {/* Hotel results table */}
      <Sequence from={60} durationInFrames={240} layout="none">
        <div style={{ marginLeft: "24px" }}>
          <TerminalTable
            columns={columns}
            rows={rows}
            entranceDelay={0}
            rowStagger={8}
          />
        </div>
      </Sequence>

      {/* Feature badges - terminal style with brackets */}
      <Sequence from={180} durationInFrames={120} layout="none">
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "24px",
            marginTop: "auto",
            fontFamily: TERMINAL_FONT,
            fontSize: "14px",
            opacity: interpolate(
              frame - 180,
              [0, 25],
              [0, 1],
              { extrapolateRight: "clamp" }
            ),
          }}
        >
          {[
            { text: "30+ cities" },
            { text: "verified ratings" },
            { text: "best price" },
          ].map((feature, i) => {
            const featureProgress = spring({
              frame: frame - 180 - i * 10,
              fps,
              config: SPRINGS.snappy,
            });

            return (
              <div
                key={i}
                style={{
                  padding: "8px 16px",
                  border: `1px solid ${COLORS.terminalBorder}`,
                  transform: `scale(${interpolate(featureProgress, [0, 1], [0.8, 1])})`,
                  opacity: interpolate(featureProgress, [0, 1], [0, 1], {
                    extrapolateRight: "clamp",
                  }),
                }}
              >
                <span style={{ color: COLORS.accent }}>[</span>
                <span style={{ color: COLORS.textSecondary }}>{feature.text}</span>
                <span style={{ color: COLORS.accent }}>]</span>
              </div>
            );
          })}
        </div>
      </Sequence>
    </AbsoluteFill>
  );
};
