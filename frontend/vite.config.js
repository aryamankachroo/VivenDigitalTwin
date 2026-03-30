import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  // Fast Refresh has been flaky in some Windows setups with Vite 8.
  // Disable it to avoid runtime crashes that prevent auth flow from completing.
  plugins: [react({ fastRefresh: false })],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:5000',
      '/auth': 'http://127.0.0.1:5000',
    },
  },
})
