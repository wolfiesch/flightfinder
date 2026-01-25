import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS, TERMINAL_FONT, SPRINGS } from "../styles/colors";

// Box-drawing characters
const BOX = {
  topLeft: "┌",
  topRight: "┐",
  bottomLeft: "└",
  bottomRight: "┘",
  horizontal: "─",
  vertical: "│",
  teeDown: "┬",
  teeUp: "┴",
  teeRight: "├",
  teeLeft: "┤",
  cross: "┼",
};

interface Column {
  header: string;
  key: string;
  width: number;
  align?: "left" | "right" | "center";
}

interface TableRow {
  [key: string]: string | number | boolean | undefined;
  highlighted?: boolean;
  annotation?: string;
}

interface TerminalTableProps {
  columns: Column[];
  rows: TableRow[];
  entranceDelay?: number;
  rowStagger?: number;
  highlightColor?: string;
}

// Pad string to width with alignment
const padString = (
  str: string,
  width: number,
  align: "left" | "right" | "center" = "left"
): string => {
  const strLen = str.length;
  if (strLen >= width) return str.slice(0, width);

  const padding = width - strLen;
  switch (align) {
    case "right":
      return " ".repeat(padding) + str;
    case "center":
      const left = Math.floor(padding / 2);
      const right = padding - left;
      return " ".repeat(left) + str + " ".repeat(right);
    default:
      return str + " ".repeat(padding);
  }
};

// Build horizontal line
const buildHorizontalLine = (
  columns: Column[],
  left: string,
  middle: string,
  right: string
): string => {
  return (
    left +
    columns.map((col) => BOX.horizontal.repeat(col.width + 2)).join(middle) +
    right
  );
};

// Build row line
const buildRowLine = (columns: Column[], values: string[], isHighlighted = false): React.ReactNode => {
  const cells = columns.map((col, i) => {
    const value = padString(values[i] || "", col.width, col.align);
    return ` ${value} `;
  });

  return (
    <>
      <span style={{ color: COLORS.terminalBorder }}>{BOX.vertical}</span>
      {cells.map((cell, i) => (
        <React.Fragment key={i}>
          <span style={{ color: isHighlighted ? COLORS.success : COLORS.textPrimary }}>
            {cell}
          </span>
          <span style={{ color: COLORS.terminalBorder }}>{BOX.vertical}</span>
        </React.Fragment>
      ))}
    </>
  );
};

export const TerminalTable: React.FC<TerminalTableProps> = ({
  columns,
  rows,
  entranceDelay = 0,
  rowStagger = 8,
  highlightColor = COLORS.success,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Header entrance
  const headerProgress = spring({
    frame: frame - entranceDelay,
    fps,
    config: SPRINGS.snappy,
  });

  const headerOpacity = interpolate(headerProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Build table structure
  const topLine = buildHorizontalLine(columns, BOX.topLeft, BOX.teeDown, BOX.topRight);
  const separatorLine = buildHorizontalLine(columns, BOX.teeRight, BOX.cross, BOX.teeLeft);
  const bottomLine = buildHorizontalLine(columns, BOX.bottomLeft, BOX.teeUp, BOX.bottomRight);

  return (
    <div
      style={{
        fontFamily: TERMINAL_FONT,
        fontSize: "16px",
        lineHeight: 1.4,
        whiteSpace: "pre",
      }}
    >
      {/* Top border */}
      <div style={{ color: COLORS.terminalBorder, opacity: headerOpacity }}>
        {topLine}
      </div>

      {/* Header row */}
      <div style={{ opacity: headerOpacity }}>
        {buildRowLine(
          columns,
          columns.map((col) => col.header),
          false
        )}
      </div>

      {/* Header separator */}
      <div style={{ color: COLORS.terminalBorder, opacity: headerOpacity }}>
        {separatorLine}
      </div>

      {/* Data rows */}
      {rows.map((row, rowIndex) => {
        const rowDelay = entranceDelay + 15 + rowIndex * rowStagger;
        const rowProgress = spring({
          frame: frame - rowDelay,
          fps,
          config: SPRINGS.snappy,
        });

        const rowOpacity = interpolate(rowProgress, [0, 1], [0, 1], {
          extrapolateRight: "clamp",
        });
        const translateX = interpolate(rowProgress, [0, 1], [-10, 0]);

        const isHighlighted = row.highlighted === true;
        const values = columns.map((col) => String(row[col.key] || ""));

        return (
          <div
            key={rowIndex}
            style={{
              opacity: rowOpacity,
              transform: `translateX(${translateX}px)`,
            }}
          >
            {buildRowLine(columns, values, isHighlighted)}
            {/* Annotation for highlighted rows */}
            {isHighlighted && row.annotation && (
              <span
                style={{
                  color: COLORS.success,
                  marginLeft: "8px",
                  fontSize: "14px",
                }}
              >
                {"<-- "}
                {row.annotation}
              </span>
            )}
          </div>
        );
      })}

      {/* Bottom border */}
      <div
        style={{
          color: COLORS.terminalBorder,
          opacity: interpolate(
            spring({
              frame: frame - entranceDelay - 15 - rows.length * rowStagger,
              fps,
              config: SPRINGS.snappy,
            }),
            [0, 1],
            [0, 1],
            { extrapolateRight: "clamp" }
          ),
        }}
      >
        {bottomLine}
      </div>
    </div>
  );
};

// Simplified receipt-style box for trip summaries
interface ReceiptBoxProps {
  title: string;
  items: Array<{ icon: string; label: string; sublabel?: string; value: string }>;
  total: { label: string; value: string };
  entranceDelay?: number;
}

export const ReceiptBox: React.FC<ReceiptBoxProps> = ({
  title,
  items,
  total,
  entranceDelay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entranceProgress = spring({
    frame: frame - entranceDelay,
    fps,
    config: SPRINGS.smooth,
  });

  const opacity = interpolate(entranceProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });

  const maxLabelWidth = 32;
  const valueWidth = 8;
  const totalWidth = maxLabelWidth + valueWidth + 4;

  const horizontalLine = "─".repeat(totalWidth);
  const titlePadded = padString(title, totalWidth - 2, "center");

  return (
    <div
      style={{
        fontFamily: TERMINAL_FONT,
        fontSize: "16px",
        lineHeight: 1.5,
        whiteSpace: "pre",
        opacity,
      }}
    >
      {/* Top rounded border */}
      <div style={{ color: COLORS.terminalBorder }}>╭{horizontalLine}╮</div>

      {/* Title */}
      <div>
        <span style={{ color: COLORS.terminalBorder }}>│</span>
        <span style={{ color: COLORS.textPrimary, fontWeight: 600 }}> {titlePadded} </span>
        <span style={{ color: COLORS.terminalBorder }}>│</span>
      </div>

      {/* Title separator */}
      <div style={{ color: COLORS.terminalBorder }}>├{horizontalLine}┤</div>

      {/* Line items */}
      {items.map((item, index) => {
        const itemDelay = entranceDelay + 15 + index * 10;
        const itemProgress = spring({
          frame: frame - itemDelay,
          fps,
          config: SPRINGS.snappy,
        });

        const itemOpacity = interpolate(itemProgress, [0, 1], [0, 1], {
          extrapolateRight: "clamp",
        });

        const label = `${item.icon} ${item.label}`;
        const paddedLabel = padString(label, maxLabelWidth, "left");
        const paddedValue = padString(item.value, valueWidth, "right");

        return (
          <div key={index} style={{ opacity: itemOpacity }}>
            <span style={{ color: COLORS.terminalBorder }}>│</span>
            <span style={{ color: COLORS.textPrimary }}> {paddedLabel}</span>
            <span style={{ color: COLORS.textSecondary }}>{paddedValue} </span>
            <span style={{ color: COLORS.terminalBorder }}>│</span>
            {item.sublabel && (
              <div>
                <span style={{ color: COLORS.terminalBorder }}>│</span>
                <span style={{ color: COLORS.textDim }}>
                  {"   "}
                  {padString(item.sublabel, maxLabelWidth + valueWidth - 1, "left")}
                </span>
                <span style={{ color: COLORS.terminalBorder }}>│</span>
              </div>
            )}
          </div>
        );
      })}

      {/* Total separator */}
      <div style={{ color: COLORS.terminalBorder }}>├{horizontalLine}┤</div>

      {/* Total */}
      {(() => {
        const totalDelay = entranceDelay + 15 + items.length * 10 + 10;
        const totalProgress = spring({
          frame: frame - totalDelay,
          fps,
          config: SPRINGS.bouncy,
        });

        const totalOpacity = interpolate(totalProgress, [0, 1], [0, 1], {
          extrapolateRight: "clamp",
        });
        const totalScale = interpolate(totalProgress, [0, 1], [0.8, 1]);

        const paddedLabel = padString(total.label, maxLabelWidth, "left");
        const paddedValue = padString(total.value, valueWidth, "right");

        return (
          <div style={{ opacity: totalOpacity, transform: `scale(${totalScale})`, transformOrigin: "left" }}>
            <span style={{ color: COLORS.terminalBorder }}>│</span>
            <span style={{ color: COLORS.textPrimary, fontWeight: 700 }}> {paddedLabel}</span>
            <span style={{ color: COLORS.success, fontWeight: 700 }}>{paddedValue} </span>
            <span style={{ color: COLORS.terminalBorder }}>│</span>
          </div>
        );
      })()}

      {/* Bottom rounded border */}
      <div style={{ color: COLORS.terminalBorder }}>╰{horizontalLine}╯</div>
    </div>
  );
};
