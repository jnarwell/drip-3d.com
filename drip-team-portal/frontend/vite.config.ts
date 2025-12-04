import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000
  },
  build: {
    // Ensure assets are copied properly
    assetsInclude: ['**/*.jpg', '**/*.jpeg', '**/*.png', '**/*.svg'],
    // Copy public folder contents
    copyPublicDir: true
  },
  publicDir: 'public'
})
