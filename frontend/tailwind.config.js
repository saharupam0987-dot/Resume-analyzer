/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['Newsreader', 'Fraunces', 'Georgia', 'serif'],
        display: ['Newsreader', 'Fraunces', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        canvas: '#FAF8F5',
        surface: {
          DEFAULT: '#FFFFFF',
          subtle: '#FAF8F5',
          warm: '#F5F2EA',
        },
        pine: {
          50: '#F0F5F2',
          100: '#E1ECE5',
          200: '#C3D9CC',
          500: '#235845',
          DEFAULT: '#16382C',
          600: '#133227',
          700: '#0E271E',
          800: '#091A14',
          900: '#050E0B',
        },
        terracotta: {
          50: '#FDF4F1',
          100: '#FBE6E0',
          500: '#E05D38',
          DEFAULT: '#E05D38',
          hover: '#C94B27',
          600: '#C94B27',
          700: '#A43A1C',
        },
        sage: {
          50: '#F4F7F5',
          100: '#E8EFE9',
          DEFAULT: '#E8EFE9',
          border: '#D0DDD2',
          dark: '#355240',
        },
        charcoal: {
          DEFAULT: '#1C2421',
          muted: '#66706B',
          faint: '#9BA49F',
        },
        editorial: {
          border: '#E7E4DC',
          'border-strong': '#D8D4C8',
        }
      },
    },
  },
  plugins: [],
}