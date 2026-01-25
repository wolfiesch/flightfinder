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
import { GradientText } from "../components/GradientText";
import { GradientBorder } from "../components/GradientBorder";
import { GradientGlow } from "../components/GradientGlow";

/**
 * CTAScene - 240 frames (8 seconds)
 * Premium call to action with gradients everywhere
 *
 * Timeline:
 * - Frame 0-30: Main text entrance
 * - Frame 30-60: Install command box
 * - Frame 60-120: Badges appear
 * - Frame 120-240: Persistent with cursor blink
 */
export const CTAScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Main CTA entrance
  const ctaProgress = spring({
    frame,
    fps,
    config: SPRINGS.premium,
  });

  const ctaOpacity = interpolate(ctaProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const ctaY = interpolate(ctaProgress, [0, 1], [30, 0]);
  const ctaScale = interpolate(ctaProgress, [0, 1], [0.95, 1]);

  // Command box entrance
  const codeProgress = spring({
    frame: frame - 25,
    fps,
    config: SPRINGS.snappy,
  });

  const codeOpacity = interpolate(codeProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const codeScale = interpolate(codeProgress, [0, 1], [0.9, 1]);

  // Blinking cursor - persistent
  const cursorVisible = Math.floor(frame / 15) % 2 === 0;

  // Background glow intensity
  const glowIntensity = interpolate(
    Math.sin(frame * 0.03) * 0.5 + 0.5,
    [0, 1],
    [0.1, 0.18]
  );

  const badges = [
    { text: "open-source", delay: 55 },
    { text: "free", delay: 65 },
    { text: "no-api-key", delay: 75 },
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
      }}
    >
      {/* Large radial glow background */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `
            radial-gradient(ellipse 80% 60% at 50% 40%, rgba(0, 212, 255, ${glowIntensity * 0.5}) 0%, transparent 50%),
            radial-gradient(ellipse 60% 80% at 50% 60%, rgba(168, 85, 247, ${glowIntensity}) 0%, transparent 50%)
          `,
          pointerEvents: "none",
        }}
      />

      {/* Main headline with gradient text */}
      <div
        style={{
          textAlign: "center",
          opacity: ctaOpacity,
          transform: `translateY(${ctaY}px) scale(${ctaScale})`,
        }}
      >
        <GradientText fontSize={56} fontWeight={800} animate={true} glow={true}>
          One command. No API key.
        </GradientText>
      </div>

      {/* Install command with gradient border */}
      <div
        style={{
          transform: `scale(${codeScale})`,
          opacity: codeOpacity,
        }}
      >
        <GradientGlow intensity={0.8} animate={true} style={{ borderRadius: "12px" }}>
          <GradientBorder width={2} borderRadius={12} animate={true}>
            <div
              style={{
                padding: "20px 40px",
              }}
            >
              <div
                style={{
                  fontFamily: TERMINAL_FONT,
                  fontSize: "22px",
                  color: COLORS.textPrimary,
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                }}
              >
                <span style={{ color: COLORS.success }}>$</span>
                <span>npx skills install flightfinder</span>
                {cursorVisible && (
                  <span
                    style={{
                      display: "inline-block",
                      width: "12px",
                      height: "22px",
                      backgroundColor: COLORS.cyan,
                      boxShadow: `0 0 10px ${COLORS.cyan}`,
                    }}
                  />
                )}
              </div>
            </div>
          </GradientBorder>
        </GradientGlow>
      </div>

      {/* Badges with gradient borders */}
      <div
        style={{
          display: "flex",
          gap: "20px",
          marginTop: "8px",
        }}
      >
        {badges.map((badge, index) => {
          const badgeProgress = spring({
            frame: frame - badge.delay,
            fps,
            config: SPRINGS.bouncy,
          });

          const badgeOpacity = interpolate(badgeProgress, [0, 1], [0, 1], {
            extrapolateRight: "clamp",
          });
          const badgeScale = interpolate(badgeProgress, [0, 1], [0.5, 1]);

          return (
            <div
              key={index}
              style={{
                opacity: badgeOpacity,
                transform: `scale(${badgeScale})`,
              }}
            >
              <div
                style={{
                  padding: "10px 20px",
                  borderRadius: "20px",
                  background: `linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(168, 85, 247, 0.1))`,
                  border: `1px solid rgba(168, 85, 247, 0.3)`,
                  fontFamily: TERMINAL_FONT,
                  fontSize: "14px",
                }}
              >
                <span style={{ color: COLORS.purple }}>[</span>
                <span style={{ color: COLORS.textSecondary }}>{badge.text}</span>
                <span style={{ color: COLORS.purple }}>]</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Logo watermark - minimal */}
      <Sequence from={100} durationInFrames={140}>
        <div
          style={{
            position: "absolute",
            bottom: "50px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            fontFamily: "Inter, -apple-system, sans-serif",
            opacity: interpolate(
              frame - 100,
              [0, 20],
              [0, 0.6],
              { extrapolateRight: "clamp" }
            ),
          }}
        >
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "50%",
              background: `linear-gradient(135deg, ${COLORS.cyan}, ${COLORS.purple})`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "16px",
              fontWeight: 800,
              color: COLORS.bg,
            }}
          >
            FF
          </div>
          <span
            style={{
              fontSize: "18px",
              fontWeight: 600,
              color: COLORS.textSecondary,
            }}
          >
            FlightFinder
          </span>
        </div>
      </Sequence>
    </AbsoluteFill>
  );
};
