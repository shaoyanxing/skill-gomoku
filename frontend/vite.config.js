import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/gomoku/',
  server: {
    port: 5173,
    proxy: {
      '/gomoku/api': { target: 'http://localhost:8000', rewrite: p => p.replace(/^\/gomoku\/api/, '/api') },
      '/gomoku/ws': { target: 'ws://localhost:8000', ws: true, rewrite: p => p.replace(/^\/gomoku\/ws/, '/ws') },
    },
  },
})
