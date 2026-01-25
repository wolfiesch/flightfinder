import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  Sequence,
} from "remotion";
import { COLORS, TERMINAL_FONT } from "../styles/colors";
import { TerminalPrompt } from "../components/TerminalPrompt";
import { TerminalTable } from "../components/TerminalTable";

export const FlightSearchScene: React.FC = () => {
  const frame = useCurrentFrame();

  // Flight data for the terminal table
  const columns = [
    { header: "ROUTE", key: "route", width: 14, align: "left" as const },
    { header: "AIRLINE", key: "airline", width: 10, align: "left" as const },
    { header: "DURATION", key: "duration", width: 10, align: "center" as const },
    { header: "PRICE", key: "price", width: 8, align: "right" as const },
  ];

  const rows = [
    { route: "SFO → TYO", airline: "JAL", duration: "11h 15m", price: "$489" },
    { route: "SFO → LHR", airline: "United", duration: "10h 30m", price: "$412" },
    { route: "SFO → Anywhere", airline: "Multi", duration: "Various", price: "$89", highlighted: true, annotation: "best" },
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
        # Flight Search
      </div>

      {/* Terminal-style prompts */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "16px",
        }}
      >
        {/* User prompt */}
        <Sequence from={10} durationInFrames={350} layout="none">
          <TerminalPrompt
            message="Find me the cheapest flights from SFO"
            isUser={true}
            entranceDelay={0}
          />
        </Sequence>

        {/* Claude response */}
        <Sequence from={45} durationInFrames={320} layout="none">
          <TerminalPrompt
            message="Searching flights from San Francisco..."
            isUser={false}
            entranceDelay={0}
          />
        </Sequence>

        {/* Results table */}
        <Sequence from={75} durationInFrames={290} layout="none">
          <div style={{ marginLeft: "24px" }}>
            <TerminalTable
              columns={columns}
              rows={rows}
              entranceDelay={0}
              rowStagger={10}
            />
          </div>
        </Sequence>

        {/* Highlight callout - terminal style */}
        <Sequence from={150} durationInFrames={215} layout="none">
          <div
            style={{
              marginLeft: "24px",
              fontFamily: TERMINAL_FONT,
              fontSize: "16px",
              opacity: interpolate(
                frame - 150,
                [0, 20],
                [0, 1],
                { extrapolateRight: "clamp" }
              ),
            }}
          >
            <span style={{ color: COLORS.accent }}>{">>> "}</span>
            <span style={{ color: COLORS.textSecondary }}>
              'Anywhere' search finds hidden deals
            </span>
          </div>
        </Sequence>
      </div>

      {/* Bottom stats - terminal style */}
      <Sequence from={180} durationInFrames={185} layout="none">
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "40px",
            paddingTop: "20px",
            borderTop: `1px solid ${COLORS.terminalBorder}`,
            fontFamily: TERMINAL_FONT,
            opacity: interpolate(
              frame - 180,
              [0, 30],
              [0, 1],
              { extrapolateRight: "clamp" }
            ),
          }}
        >
          {[
            { label: "destinations", value: "10,000+" },
            { label: "airlines", value: "500+" },
            { label: "data", value: "real-time" },
          ].map((stat, i) => (
            <div
              key={i}
              style={{
                textAlign: "center",
              }}
            >
              <div
                style={{
                  fontSize: "24px",
                  fontWeight: 700,
                  color: COLORS.accent,
                }}
              >
                {stat.value}
              </div>
              <div
                style={{
                  fontSize: "12px",
                  color: COLORS.textDim,
                  textTransform: "lowercase",
                }}
              >
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </Sequence>
    </AbsoluteFill>
  );
};
