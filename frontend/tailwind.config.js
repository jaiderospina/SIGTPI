/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary:  { DEFAULT: '#1F3864', 50: '#EBF5FB', 100: '#D6EAF8', 500: '#2E74B5', 700: '#1F3864' },
        success:  { DEFAULT: '#148F77', light: '#D1F2EB' },
        warning:  { DEFAULT: '#D68910', light: '#FEF0C7' },
        danger:   { DEFAULT: '#C0392B', light: '#FADBD8' },
        info:     { DEFAULT: '#6C3DB5', light: '#E8DAEF' },
      }
    }
  },
  plugins: []
}
