/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{ts,tsx,html}'],
  theme: {
    extend: {
      colors: {
        // FlightFinder design system
        ff: {
          bg: '#030014',
          'bg-secondary': '#0a0118',
          terminal: '#0d0d1a',
          'terminal-border': '#1e1e3f',
          cyan: '#00d4ff',
          purple: '#a855f7',
          pink: '#ec4899',
          accent: '#00d4ff',
          'accent-dim': '#0099cc',
          success: '#3fb950',
          warning: '#d29922',
          error: '#f85149',
          'text-primary': '#e6edf3',
          'text-secondary': '#8b949e',
          'text-dim': '#484f58',
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "'SF Mono'", "'Fira Code'", 'monospace'],
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #00d4ff 0%, #a855f7 50%, #ec4899 100%)',
        'gradient-horizontal': 'linear-gradient(90deg, #00d4ff 0%, #a855f7 50%, #ec4899 100%)',
        'gradient-radial': 'radial-gradient(ellipse at center, rgba(168, 85, 247, 0.15) 0%, transparent 70%)',
      },
      boxShadow: {
        glow: '0 0 40px rgba(0, 212, 255, 0.3), 0 0 80px rgba(168, 85, 247, 0.2), 0 0 120px rgba(236, 72, 153, 0.1)',
        'glow-subtle': '0 0 20px rgba(168, 85, 247, 0.2)',
      },
    },
  },
  plugins: [],
};
