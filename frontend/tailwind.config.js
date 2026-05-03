/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          deep: '#050816',
          mid: '#071226',
          light: '#0A0F1F',
        },
        neon: {
          blue: '#00BFFF',
          purple: '#7A5CFF',
          violet: '#A855F7',
          cyan: '#00E5FF',
          pink: '#FF4D9D',
        }
      },
      borderRadius: {
        '2xl': '20px',
        '3xl': '32px',
      },
      boxShadow: {
        'neon-blue': '0 0 10px rgba(0, 191, 255, 0.3), 0 0 20px rgba(0, 191, 255, 0.1)',
        'neon-purple': '0 0 10px rgba(122, 92, 255, 0.3), 0 0 20px rgba(122, 92, 255, 0.1)',
      }
    },
  },
  plugins: [],
}
