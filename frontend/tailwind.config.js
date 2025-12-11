/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#020617',      
          cyan: '#06b6d4',      
          neon: '#22d3ee',      
          surface: '#ffffff',   
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'sans-serif'], // NEW FONT
      },
      boxShadow: {
        'glass': '0 12px 40px 0 rgba(0, 0, 0, 0.15)',
        'clean': '0 2px 8px 0 rgba(0, 0, 0, 0.04)',
      }
    },
  },
  plugins: [],
}