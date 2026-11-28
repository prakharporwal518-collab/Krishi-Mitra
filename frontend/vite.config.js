import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    // Installable app that works offline: the model, its runtime, the knowledge base and samples are cached
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icons/*.png', 'samples/*.jpg'],
      manifest: {
        name: 'Krishi Mitra – Crop Doctor',
        short_name: 'Krishi Mitra',
        description: 'Multilingual crop disease diagnosis and treatment for Indian farmers',
        theme_color: '#15803d',
        background_color: '#f0fdf4',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,mjs,css,html,png,jpg,svg,wasm,onnx,json}'],
        maximumFileSizeToCacheInBytes: 30 * 1024 * 1024, // model (~9 MB) and ONNX Runtime wasm (~11 MB)
        navigateFallback: '/index.html',
        runtimeCaching: [
          { urlPattern: /^https:\/\/fonts\.(googleapis|gstatic)\.com\//, handler: 'CacheFirst', options: { cacheName: 'fonts', expiration: { maxEntries: 20 } } },
        ],
      },
    }),
  ],
  server: {
    host: true,
    port: 5173,
    proxy: { '/api': process.env.VITE_BACKEND_URL || 'http://localhost:8000' },
  },
})
