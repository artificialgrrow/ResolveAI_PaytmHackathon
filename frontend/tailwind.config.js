/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#171717",
        canvas: "#fafafa",
        elevated: "#ffffff",
        hairline: "#ebebeb",
        hairlineSoft: "#f2f2f2",
        bodyText: "#4d4d4d",
        mute: "#8f8f8f",
        faint: "#a1a1a1",
        accentBlue: "#0070f3",
        accentBlueDeep: "#0761d1",
        accentBlueSoft: "#d3e5ff",
      },
      borderRadius: {
        sm: "6px",
        md: "12px",
        lg: "16px",
        pill: "100px",
      },
      fontFamily: {
        sans: ['Geist', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        whisper: "0 1px 1px rgba(0, 0, 0, 0.04)",
        floating: "0 2px 4px rgba(0, 0, 0, 0.04), 0 8px 16px -4px rgba(0, 0, 0, 0.06)",
      }
    },
  },
  plugins: [],
}

