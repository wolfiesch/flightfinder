/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Dark terminal aesthetic
        bg: "#0f0f23",
        terminal: "#1a1a2e",
        "terminal-border": "#2d2d4a",
        // Accent colors
        accent: "#00d4ff",
        "accent-dim": "#00a8cc",
        price: "#ff6b6b",
        "price-dim": "#cc5555",
        success: "#4ade80",
        warning: "#fbbf24",
        // Text colors
        "text-primary": "#ffffff",
        "text-secondary": "#a0a0b0",
        "text-dim": "#6b6b7b",
        // Chat bubble colors
        "chat-ai": "#1e3a5f",
        "chat-user": "#2d4a2e",
      },
      fontFamily: {
        mono: [
          "JetBrains Mono",
          "Fira Code",
          "SF Mono",
          "Monaco",
          "Consolas",
          "monospace",
        ],
        sans: ["Inter", "SF Pro Display", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(0, 212, 255, 0.3)",
        "glow-strong": "0 0 40px rgba(0, 212, 255, 0.5)",
        terminal: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
      },
    },
  },
  plugins: [],
};
