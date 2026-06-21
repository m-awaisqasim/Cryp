import { defineConfig } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

const LOGGER = {
  warn(msg) { if (msg.includes('ws proxy socket error')) return; console.warn(msg); },
  error(msg) { if (msg.includes('ws proxy socket error')) return; console.error(msg); },
  info(msg) { console.info(msg); },
  warnOnce(msg) { this.warn(msg); },
}

export default defineConfig({
  customLogger: LOGGER,
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  assetsInclude: ['**/*.svg', '**/*.csv'],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/ws': { target: `ws://localhost:${process.env.DASHBOARD_PORT || 7073}`, ws: true },
      '/api': { target: `http://localhost:${process.env.DASHBOARD_PORT || 7073}` },
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  }
})
