/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],
  theme: {
    extend: {
      colors: {
        'alert-red': '#DC2626',
        'alert-yellow': '#D97706',
        'alert-green': '#059669',
        'security-blue': '#2563EB',
      },
      animation: {
        'pulse-slow': 'pulse 2s ease-in-out infinite',
        'bounce-subtle': 'bounce 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}