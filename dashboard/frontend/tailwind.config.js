export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        hud: {
          bg: '#00060a',
          'bg-grad': '#001018',
          panel: '#010d14',
          panel2: '#010f18',
          border: '#0d3347',
          'border-b': '#1a5c7a',
          'border-a': '#0f4060',
          pri: '#00d4ff',
          'pri-light': '#66e8ff',
          'pri-dim': '#007a99',
          'pri-gho': '#001f2e',
          acc: '#ff6b00',
          'acc-dim': '#993d00',
          acc2: '#ffcc00',
          'acc2-dim': '#997700',
          green: '#00ff88',
          'green-d': '#00aa55',
          'green-dim': '#005533',
          red: '#ff3355',
          'red-dim': '#991e33',
          muted: '#ff3366',
          text: '#8ffcff',
          'text-dim': '#3a8a9a',
          'text-med': '#5ab8cc',
          white: '#d8f8ff',
          dark: '#000d14',
          'bar-bg': '#011520',
        }
      },
      fontFamily: {
        mono: ['"Courier New"', 'monospace'],
      },
      animation: {
        'pulse-dot': 'pulse-dot 0.6s ease-in-out infinite',
        'scan': 'scan 6s linear infinite',
      },
      keyframes: {
        'pulse-dot': {
          '0%,100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
        scan: {
          '0%': { top: '0%' },
          '100%': { top: '100%' },
        },
      }
    }
  },
  plugins: []
}
