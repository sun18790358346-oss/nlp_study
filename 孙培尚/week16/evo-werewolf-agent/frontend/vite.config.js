import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/games': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/configs': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
