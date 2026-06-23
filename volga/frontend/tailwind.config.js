/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js}'
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          'Karla',
          'Source Sans Pro',
          'Segoe UI',
          'Arial',
          'system-ui',
          'sans-serif'
        ],
        montserrat: [
          'Montserrat',
          'Karla',
          'Source Sans Pro',
          'Segoe UI',
          'Arial',
          'system-ui',
          'sans-serif'
        ],
        source: [
          'Source Sans Pro',
          'Karla',
          'Segoe UI',
          'Arial',
          'system-ui',
          'sans-serif'
        ],
        segoe: ['Segoe UI', 'Arial', 'system-ui', 'sans-serif']
      }
    }
  },
  plugins: []
}
