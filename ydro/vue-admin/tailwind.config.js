/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f4f1ff',
          100: '#ebe7ff',
          200: '#d8d0ff',
          300: '#b8a8ff',
          400: '#967cff',
          500: '#7c63ff',
          600: '#6d5df6',
          700: '#5b49f5',
          800: '#4939d2',
          900: '#3d31a7',
          950: '#251f61',
        },
      },
      boxShadow: {
        soft: '0 10px 35px rgba(32, 40, 70, 0.08)',
      },
    },
  },
  plugins: [],
}
