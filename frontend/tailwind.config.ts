import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0a0e1a',
          secondary: '#0f1629',
          card: '#141d35',
          elevated: '#1a2540',
        },
        border: {
          DEFAULT: '#1e3a5f',
        },
        accent: {
          DEFAULT: '#00d4ff',
          green: '#00ff88',
          red: '#ff3366',
          orange: '#ff8c42',
          yellow: '#ffd700',
        },
        text: {
          primary: '#e2e8f0',
          secondary: '#94a3b8',
          muted: '#4a5568',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      },
      backgroundImage: {
        'grid-pattern':
          'linear-gradient(rgba(30,58,95,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(30,58,95,0.15) 1px, transparent 1px)',
      },
      backgroundSize: {
        grid: '32px 32px',
      },
      boxShadow: {
        glow: '0 0 20px rgba(0, 212, 255, 0.25)',
        'glow-red': '0 0 20px rgba(255, 51, 102, 0.25)',
        'glow-green': '0 0 20px rgba(0, 255, 136, 0.25)',
      },
      keyframes: {
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
      },
      animation: {
        scanline: 'scanline 6s linear infinite',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
export default config
