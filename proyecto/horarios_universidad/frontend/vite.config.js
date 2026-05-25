import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '^/api/': {
        // Local FastAPI backend — run: uvicorn scheduler.interfaces.api.main:app --port 8000
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Solver can run up to 6000s; give 2 min buffer
        timeout: 6200000,
        proxyTimeout: 6200000,
      },
    },
  },
})
