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

export const AIIntegrationScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // MCP server visualization
  const mcpProgress = spring({
    frame,
    fps,
    config: SPRINGS.smooth,
  });

  // Platform clients
  const platforms = [
    { name: "claude", id: "claude", delay: 30 },
    { name: "vercel-ai", id: "vercel", delay: 45 },
    { name: "langchain", id: "langchain", delay: 60 },
    { name: "any-mcp-client", id: "mcp", delay: 75 },
  ];

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "40px",
        fontFamily: TERMINAL_FONT,
      }}
    >
      {/* Title - terminal style */}
      <div
        style={{
          fontSize: "32px",
          fontWeight: 600,
          color: COLORS.textPrimary,
          textAlign: "center",
          opacity: interpolate(mcpProgress, [0, 1], [0, 1], {
            extrapolateRight: "clamp",
          }),
        }}
      >
        Works with any{" "}
        <span style={{ color: COLORS.accent }}>MCP-compatible</span> AI
      </div>

      {/* ASCII-style architecture diagram */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "24px",
          opacity: interpolate(mcpProgress, [0, 1], [0, 1], {
            extrapolateRight: "clamp",
          }),
        }}
      >
        {/* Client nodes row */}
        <div style={{ display: "flex", gap: "20px" }}>
          {platforms.map((platform, index) => {
            const nodeProgress = spring({
              frame: frame - platform.delay,
              fps,
              config: SPRINGS.snappy,
            });

            return (
              <div
                key={index}
                style={{
                  opacity: interpolate(nodeProgress, [0, 1], [0, 1], {
                    extrapolateRight: "clamp",
                  }),
                  transform: `translateY(${interpolate(nodeProgress, [0, 1], [10, 0])}px)`,
                }}
              >
                {/* Terminal-style node box */}
                <div
                  style={{
                    border: `1px solid ${COLORS.terminalBorder}`,
                    padding: "12px 16px",
                    minWidth: "140px",
                    textAlign: "center",
                  }}
                >
                  <div style={{ color: COLORS.textSecondary, fontSize: "14px" }}>
                    {platform.name}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Connection lines - ASCII style */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            color: COLORS.terminalBorder,
            fontSize: "14px",
            lineHeight: 1.2,
            opacity: interpolate(frame, [50, 80], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          <div style={{ whiteSpace: "pre" }}>
            {"    │          │          │          │    "}
          </div>
          <div style={{ whiteSpace: "pre" }}>
            {"    └──────────┴────┬─────┴──────────┘    "}
          </div>
          <div style={{ whiteSpace: "pre" }}>
            {"                    │                     "}
          </div>
          <div style={{ whiteSpace: "pre" }}>
            {"                    ▼                     "}
          </div>
        </div>

        {/* Center - FlightFinder MCP Server */}
        <div
          style={{
            transform: `scale(${interpolate(mcpProgress, [0, 1], [0.9, 1])})`,
          }}
        >
          <div
            style={{
              border: `2px solid ${COLORS.accent}`,
              padding: "20px 32px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                fontSize: "18px",
                fontWeight: 600,
                color: COLORS.textPrimary,
                marginBottom: "4px",
              }}
            >
              flightfinder
            </div>
            <div style={{ color: COLORS.accent, fontSize: "12px" }}>
              MCP Server
            </div>
          </div>
        </div>

        {/* API connections below */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            color: COLORS.terminalBorder,
            fontSize: "14px",
            lineHeight: 1.2,
            opacity: interpolate(frame, [70, 100], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          <div style={{ whiteSpace: "pre" }}>
            {"                    │                     "}
          </div>
          <div style={{ whiteSpace: "pre" }}>
            {"    ┌───────────────┼───────────────┐    "}
          </div>
          <div style={{ whiteSpace: "pre" }}>
            {"    │               │               │    "}
          </div>
          <div style={{ whiteSpace: "pre" }}>
            {"    ▼               ▼               ▼    "}
          </div>
        </div>

        {/* API endpoints row */}
        <div style={{ display: "flex", gap: "24px" }}>
          {[
            { name: "search_flights", delay: 90 },
            { name: "search_hotels", delay: 100 },
            { name: "find_location", delay: 110 },
          ].map((api, index) => {
            const apiProgress = spring({
              frame: frame - api.delay,
              fps,
              config: SPRINGS.snappy,
            });

            return (
              <div
                key={index}
                style={{
                  opacity: interpolate(apiProgress, [0, 1], [0, 1], {
                    extrapolateRight: "clamp",
                  }),
                  transform: `translateY(${interpolate(apiProgress, [0, 1], [10, 0])}px)`,
                }}
              >
                <div
                  style={{
                    border: `1px solid ${COLORS.terminalBorder}`,
                    padding: "8px 12px",
                    fontSize: "12px",
                    color: COLORS.success,
                  }}
                >
                  {api.name}()
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom protocol info */}
      <Sequence from={90} durationInFrames={75}>
        <div
          style={{
            fontSize: "14px",
            padding: "12px 24px",
            border: `1px solid ${COLORS.terminalBorder}`,
            opacity: interpolate(
              frame - 90,
              [0, 20],
              [0, 1],
              { extrapolateRight: "clamp" }
            ),
          }}
        >
          <span style={{ color: COLORS.textDim }}>protocol:</span>{" "}
          <span style={{ color: COLORS.accent }}>Model Context Protocol (MCP)</span>
        </div>
      </Sequence>
    </AbsoluteFill>
  );
};
