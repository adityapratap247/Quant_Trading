/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        quant: {
          bg: '#0a0e17',
          surface: '#111827',
          card: '#161f30',
          border: '#1f293d',
          accent: '#38bdf8',
          success: '#10b981',
          danger: '#f43f5e',
          warning: '#f59e0b',
          muted: '#94a3b8',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

