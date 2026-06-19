import { defineConfig } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
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
