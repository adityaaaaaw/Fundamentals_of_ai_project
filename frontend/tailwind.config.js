/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ivory: {
          50: '#FDFBF7',
          100: '#FAF6F0', // Main background
          200: '#F4ECE1',
          300: '#ECE1D0',
          400: '#DFD1BD',
          500: '#CDBCA3',
        },
        gold: {
          50: '#FBF8F1',
          100: '#F7F0E1',
          200: '#EBDCB9',
          300: '#DFC790',
          400: '#D2B368',
          500: '#C5A059', // Primary muted gold accent
          600: '#B08B44',
          700: '#926F32',
          800: '#755627',
          900: '#5F451F',
        },
        cardborder: '#EFEAE1',
      },
      fontFamily: {
        heading: ['Poppins', 'sans-serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 2px 10px rgba(0, 0, 0, 0.03), 0 1px 3px rgba(0, 0, 0, 0.02)',
        'soft-md': '0 4px 16px rgba(0, 0, 0, 0.05), 0 2px 6px rgba(0, 0, 0, 0.03)',
        'soft-lg': '0 10px 25px rgba(0, 0, 0, 0.06), 0 4px 10px rgba(0, 0, 0, 0.04)',
      }
    },
  },
  plugins: [],
}


