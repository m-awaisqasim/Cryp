import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/ws': { target: 'ws://localhost:7070', ws: true },
      '/api': { target: 'http://localhost:7070' },
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  }
})