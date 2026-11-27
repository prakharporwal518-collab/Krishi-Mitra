/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        leaf: { 50: '#f0fdf4', 100: '#dcfce7', 200: '#bbf7d0', 500: '#22c55e', 600: '#16a34a', 700: '#15803d', 800: '#166534', 900: '#14532d' },
        soil: { 100: '#fef3c7', 400: '#d97706', 700: '#78350f' },
      },
      fontFamily: { sans: ['"Noto Sans"', '"Noto Sans Devanagari"', 'system-ui', 'sans-serif'] },
    },
  },
  plugins: [],
}
