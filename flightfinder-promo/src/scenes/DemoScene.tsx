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
import { GradientGlow } from "../components/GradientGlow";
import { GradientText } from "../components/GradientText";

/**
 * DemoScene - 360 frames (12 seconds)
 * Combined flight search, hotel search, and trip total
 *
 * Timeline:
 * - Frame 0-120: Flight Search (4s)
 * - Frame 120-240: Hotel Search with slide transition (4s)
 * - Frame 240-360: Trip Total with combine animation (4s)
 */

interface TableRowData {
  cells: string[];
  highlighted?: boolean;
}

const MiniTable: React.FC<{
  headers: string[];
  rows: TableRowData[];
  entranceDelay: number;
  highlightGradient?: boolean;
}> = ({ headers, rows, entranceDelay, highlightGradient = true }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerProgress = spring({
    frame: frame - entranceDelay,
    fps,
    config: SPRINGS.snappy,
  });

  const headerOpacity = interpolate(headerProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        fontFamily: TERMINAL_FONT,
        fontSize: "14px",
        lineHeight: 1.8,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          gap: "24px",
          color: COLORS.textDim,
          borderBottom: `1px solid ${COLORS.terminalBorder}`,
          paddingBottom: "8px",
          marginBottom: "8px",
          opacity: headerOpacity,
        }}
      >
        {headers.map((h, i) => (
          <span key={i} style={{ minWidth: i === 0 ? "120px" : "80px" }}>
            {h}
          </span>
        ))}
      </div>

      {/* Rows with 3-frame stagger */}
      {rows.map((row, rowIndex) => {
        const rowDelay = entranceDelay + 10 + rowIndex * 3;
        const rowProgress = spring({
          frame: frame - rowDelay,
          fps,
          config: SPRINGS.snappy,
        });

        const rowOpacity = interpolate(rowProgress, [0, 1], [0, 1], {
          extrapolateRight: "clamp",
        });
        const translateX = interpolate(rowProgress, [0, 1], [-8, 0]);

        const isHighlighted = row.highlighted;

        return (
          <div
            key={rowIndex}
            style={{
              display: "flex",
              gap: "24px",
              opacity: rowOpacity,
              transform: `translateX(${translateX}px)`,
              padding: "4px 0",
              background: isHighlighted && highlightGradient
                ? "linear-gradient(90deg, rgba(0, 212, 255, 0.1), transparent)"
                : "transparent",
              borderLeft: isHighlighted ? `2px solid ${COLORS.cyan}` : "2px solid transparent",
              paddingLeft: "8px",
              marginLeft: "-10px",
            }}
          >
            {row.cells.map((cell, i) => (
              <span
                key={i}
                style={{
                  minWidth: i === 0 ? "120px" : "80px",
                  color: isHighlighted && i === row.cells.length - 1
                    ? COLORS.cyan
                    : COLORS.textPrimary,
                  fontWeight: isHighlighted && i === row.cells.length - 1 ? 700 : 400,
                }}
              >
                {cell}
              </span>
            ))}
          </div>
        );
      })}
    </div>
  );
};

export const DemoScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Section visibility
  const FLIGHT_START = 0;
  const HOTEL_START = 120;
  const TRIP_START = 240;

  // Flight section (0-120)
  const flightProgress = spring({
    frame: frame - FLIGHT_START,
    fps,
    config: SPRINGS.premium,
  });
  const flightOpacity = interpolate(flightProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const flightX = interpolate(
    frame,
    [HOTEL_START - 15, HOTEL_START],
    [0, -50],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const flightFadeOut = interpolate(
    frame,
    [HOTEL_START - 15, HOTEL_START],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Hotel section (120-240)
  const hotelProgress = spring({
    frame: frame - HOTEL_START,
    fps,
    config: SPRINGS.premium,
  });
  const hotelOpacity = interpolate(hotelProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const hotelX = interpolate(hotelProgress, [0, 1], [50, 0]);
  const hotelFadeOut = interpolate(
    frame,
    [TRIP_START - 15, TRIP_START],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Trip section (240-360)
  const tripProgress = spring({
    frame: frame - TRIP_START,
    fps,
    config: SPRINGS.premium,
  });
  const tripOpacity = interpolate(tripProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const tripScale = interpolate(tripProgress, [0, 1], [0.9, 1]);

  // Background glow
  const glowIntensity = interpolate(
    Math.sin(frame * 0.03) * 0.5 + 0.5,
    [0, 1],
    [0.05, 0.1]
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        padding: "60px 100px",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
      }}
    >
      {/* Background glow */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at center, rgba(168, 85, 247, ${glowIntensity}) 0%, transparent 60%)`,
          pointerEvents: "none",
        }}
      />

      {/* FLIGHT SEARCH SECTION */}
      {frame < HOTEL_START + 15 && (
        <div
          style={{
            position: "absolute",
            inset: "60px 100px",
            opacity: flightOpacity * flightFadeOut,
            transform: `translateX(${flightX}px)`,
          }}
        >
          <div style={{ color: COLORS.textDim, fontSize: "14px", marginBottom: "20px" }}>
            # Flight Search
          </div>

          <div
            style={{
              fontFamily: TERMINAL_FONT,
              fontSize: "16px",
              marginBottom: "16px",
            }}
          >
            <span style={{ color: COLORS.success }}>{">"}</span>
            <span style={{ color: COLORS.textPrimary, marginLeft: "8px" }}>
              Find cheap flights from SFO
            </span>
          </div>

          <Sequence from={30} durationInFrames={90}>
            <MiniTable
              headers={["ROUTE", "AIRLINE", "PRICE"]}
              rows={[
                { cells: ["SFO → TYO", "JAL", "$489"] },
                { cells: ["SFO → LHR", "United", "$412"] },
                { cells: ["SFO → Anywhere", "Multi", "$89"], highlighted: true },
              ]}
              entranceDelay={0}
            />
          </Sequence>

          <Sequence from={70} durationInFrames={50}>
            <div
              style={{
                marginTop: "20px",
                fontSize: "14px",
                opacity: interpolate(frame - 70, [0, 15], [0, 1], { extrapolateRight: "clamp" }),
              }}
            >
              <span style={{ color: COLORS.cyan }}>{">>>"}</span>
              <span style={{ color: COLORS.textSecondary, marginLeft: "8px" }}>
                'Anywhere' finds hidden deals
              </span>
            </div>
          </Sequence>
        </div>
      )}

      {/* HOTEL SEARCH SECTION */}
      {frame >= HOTEL_START - 15 && frame < TRIP_START + 15 && (
        <div
          style={{
            position: "absolute",
            inset: "60px 100px",
            opacity: hotelOpacity * hotelFadeOut,
            transform: `translateX(${hotelX}px)`,
          }}
        >
          <div style={{ color: COLORS.textDim, fontSize: "14px", marginBottom: "20px" }}>
            # Hotel Search
          </div>

          <div
            style={{
              fontFamily: TERMINAL_FONT,
              fontSize: "16px",
              marginBottom: "16px",
            }}
          >
            <span style={{ color: COLORS.success }}>{">"}</span>
            <span style={{ color: COLORS.textPrimary, marginLeft: "8px" }}>
              Hotels in Tokyo?
            </span>
          </div>

          <Sequence from={HOTEL_START + 25} durationInFrames={95}>
            <MiniTable
              headers={["HOTEL", "AREA", "PRICE"]}
              rows={[
                { cells: ["Park Hyatt", "Shinjuku", "$450/nt"] },
                { cells: ["Capsule Hotel", "Shibuya", "$45/nt"], highlighted: true },
              ]}
              entranceDelay={0}
            />
          </Sequence>
        </div>
      )}

      {/* TRIP TOTAL SECTION */}
      {frame >= TRIP_START - 15 && (
        <div
          style={{
            position: "absolute",
            inset: "60px 100px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            opacity: tripOpacity,
            transform: `scale(${tripScale})`,
          }}
        >
          <div style={{ color: COLORS.textDim, fontSize: "14px", marginBottom: "30px" }}>
            # Trip Summary
          </div>

          <GradientGlow intensity={1} animate={true} style={{ borderRadius: "8px" }}>
            <div
              style={{
                background: COLORS.terminal,
                border: `1px solid ${COLORS.terminalBorder}`,
                padding: "32px 48px",
                fontFamily: TERMINAL_FONT,
                fontSize: "16px",
                minWidth: "400px",
              }}
            >
              {/* Receipt items */}
              <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: COLORS.textSecondary }}>Flight (SFO → TYO)</span>
                  <span style={{ color: COLORS.textPrimary }}>$89</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: COLORS.textSecondary }}>Hotel (3 nights)</span>
                  <span style={{ color: COLORS.textPrimary }}>$135</span>
                </div>
              </div>

              {/* Divider */}
              <div
                style={{
                  borderTop: `1px solid ${COLORS.terminalBorder}`,
                  marginBottom: "16px",
                }}
              />

              {/* Total with gradient highlight */}
              <Sequence from={TRIP_START + 40} durationInFrames={80}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span style={{ color: COLORS.textPrimary, fontWeight: 600 }}>TOTAL</span>
                  <GradientText fontSize={28} fontWeight={700} animate={true}>
                    $224
                  </GradientText>
                </div>
              </Sequence>
            </div>
          </GradientGlow>

          <Sequence from={TRIP_START + 70} durationInFrames={50}>
            <div
              style={{
                marginTop: "24px",
                fontSize: "14px",
                color: COLORS.textDim,
                opacity: interpolate(frame - (TRIP_START + 70), [0, 15], [0, 1], {
                  extrapolateRight: "clamp",
                }),
              }}
            >
              Complete trip planned in seconds
            </div>
          </Sequence>
        </div>
      )}
    </AbsoluteFill>
  );
};
