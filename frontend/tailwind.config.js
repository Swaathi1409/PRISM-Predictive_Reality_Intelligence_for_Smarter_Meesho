// tailwind.config.js
// Tailwind CSS (MIT License) — utility-first styling co-located with components.
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        prism: {
          50:  '#f5f0ff',
          100: '#ede3ff',
          200: '#dccbff',
          300: '#c4a5ff',
          400: '#a875ff',
          500: '#8b45ff',
          600: '#6C2BD9',
          700: '#5820b0',
          800: '#481a90',
          900: '#3b1676',
        },
        meesho: {
          pink: '#f43397',
          orange: '#ff6a2f',
        },
        surface: {
          DEFAULT: '#0f0a1e',
          card: '#1a1230',
          elevated: '#231844',
          border: '#2d2050',
        },
      },
      backgroundImage: {
        'prism-gradient': 'linear-gradient(135deg, #6C2BD9 0%, #a855f7 50%, #f43397 100%)',
        'card-gradient': 'linear-gradient(135deg, rgba(108,43,217,0.15) 0%, rgba(168,85,247,0.08) 100%)',
        'dark-gradient': 'linear-gradient(180deg, #0f0a1e 0%, #1a1230 100%)',
        'glow-gradient': 'radial-gradient(ellipse at top, rgba(108,43,217,0.3) 0%, transparent 70%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.5s ease-out forwards',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
        'score-fill': 'scoreFill 1.5s ease-out forwards',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(20px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(108,43,217,0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(168,85,247,0.5)' },
        },
        shimmer: {
          from: { backgroundPosition: '-200% 0' },
          to: { backgroundPosition: '200% 0' },
        },
      },
      boxShadow: {
        'prism': '0 4px 32px rgba(108,43,217,0.25)',
        'prism-lg': '0 8px 48px rgba(108,43,217,0.35)',
        'card': '0 2px 16px rgba(0,0,0,0.4)',
        'glow': '0 0 30px rgba(108,43,217,0.4)',
      },
    },
  },
  plugins: [],
}
