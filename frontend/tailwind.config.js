/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Equal-weight palette for Olympic and Paralympic.
        // Olympic + Paralympic share visual weight; only the hue differs.
        olympic: {
          50: '#eff6ff',
          500: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a',
        },
        paralympic: {
          50: '#fef3c7',
          500: '#d97706',
          700: '#b45309',
          900: '#78350f',
        },
        ink: {
          50: '#f8fafc',
          200: '#e2e8f0',
          500: '#64748b',
          900: '#0f172a',
        },
      },
      fontFamily: {
        display: ['"Inter"', 'system-ui', 'sans-serif'],
        body: ['"Inter"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
