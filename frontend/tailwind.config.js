/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"DM Sans"', '"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        ink: '#03040A',
        night: '#0F0F23',
        violetDeep: '#1E1B4B',
        action: '#E11D48',
        signal: '#06B6D4',
        premium: '#F59E0B',
      },
      boxShadow: {
        glow: '0 0 48px rgba(225, 29, 72, 0.28)',
        glass: '0 24px 80px rgba(0, 0, 0, 0.35)',
      },
    },
  },
  plugins: [],
}
