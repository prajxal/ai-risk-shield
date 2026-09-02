import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/returns': 'http://127.0.0.1:8000',
      '/stream': 'http://127.0.0.1:8000',
      '/audit-logs': 'http://127.0.0.1:8000',
      '/metrics': 'http://127.0.0.1:8000',
      '/failure-case': 'http://127.0.0.1:8000',
      '/scenarios': 'http://127.0.0.1:8000',
      '/reset': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    }
  }
})
