/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx,css}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Arial', 'Poppins', 'Helvetica', 'sans-serif'],
      },
      transitionProperty: {
        'teheme': 'background-color, color, border-color'
      }
    },
  },
  plugins: [
    require('tailwind-scrollbar-hide'),
  ],
}