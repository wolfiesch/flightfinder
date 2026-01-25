// Color palette for FlightFinder promo - Premium SaaS aesthetic (Stripe/Linear style)
export const COLORS = {
  // Backgrounds - near-black with purple tint
  bg: "#030014",
  bgSecondary: "#0a0118",
  terminal: "#0d0d1a",
  terminalBorder: "#1e1e3f",

  // Multi-color gradient accents (cyan → purple → pink)
  cyan: "#00d4ff",
  purple: "#a855f7",
  pink: "#ec4899",

  // Legacy accent mapping
  accent: "#00d4ff",
  accentDim: "#0099cc",
  success: "#3fb950",
  warning: "#d29922",
  error: "#f85149",

  // Text
  textPrimary: "#e6edf3",
  textSecondary: "#8b949e",
  textDim: "#484f58",

  // Prompt colors (terminal-style)
  promptUser: "#3fb950",
  promptClaude: "#a855f7",

  // Legacy colors for backwards compatibility
  chatAI: "#1e3a5f",
  chatUser: "#2d4a2e",
  price: "#f85149",
} as const;

// Premium gradient definitions
export const GRADIENTS = {
  primary: "linear-gradient(135deg, #00d4ff 0%, #a855f7 50%, #ec4899 100%)",
  horizontal: "linear-gradient(90deg, #00d4ff 0%, #a855f7 50%, #ec4899 100%)",
  radialGlow: "radial-gradient(ellipse at center, rgba(168, 85, 247, 0.15) 0%, transparent 70%)",
  radialCyan: "radial-gradient(ellipse at center, rgba(0, 212, 255, 0.1) 0%, transparent 60%)",
} as const;

// Multi-color glow effects
export const GLOWS = {
  multi: "0 0 40px rgba(0, 212, 255, 0.3), 0 0 80px rgba(168, 85, 247, 0.2), 0 0 120px rgba(236, 72, 153, 0.1)",
  text: "0 0 20px rgba(0, 212, 255, 0.5)",
  intense: "0 0 60px rgba(0, 212, 255, 0.4), 0 0 120px rgba(168, 85, 247, 0.3), 0 0 180px rgba(236, 72, 153, 0.15)",
  subtle: "0 0 20px rgba(168, 85, 247, 0.2)",
} as const;

// Terminal font stack
export const TERMINAL_FONT = "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace";

// Spring configurations for premium, smooth animations
export const SPRINGS = {
  premium: { damping: 25, stiffness: 100, mass: 1 },
  smooth: { damping: 30, stiffness: 120 },
  snappy: { damping: 18, stiffness: 300 },
  bouncy: { damping: 12, stiffness: 200 },
  heavy: { damping: 15, stiffness: 80, mass: 2 },
} as const;

// Timing constants (in frames at 30fps)
export const FPS = 30;
export const CHAR_FRAMES = 1; // 2x faster typewriter (was 2)

// Scene frame boundaries for 30-second video (900 frames @ 30fps)
// 4 transitions × 15 frames = 60 frames overlap
// Total: 90 + 60 + 150 + 360 + 240 = 900 + 60 overlap adjustment
export const SCENES = {
  hook: { start: 0, duration: 90 },      // 0-3s: "Tired of API key hell?"
  reveal: { start: 75, duration: 75 },   // 2.5-5s: Logo + badge
  install: { start: 135, duration: 165 }, // 4.5-10s: Fast typewriter
  demo: { start: 285, duration: 375 },   // 9.5-22s: Combined flight/hotel/trip
  cta: { start: 645, duration: 255 },    // 21.5-30s: "One command. No API key."
} as const;
