import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api/auth':         { target: 'http://localhost:8001', changeOrigin: true, rewrite: p => p.replace('/api/auth', '/api/v1/auth') },
      '/api/users':        { target: 'http://localhost:8002', changeOrigin: true, rewrite: p => p.replace('/api/users', '/api/v1') },
      '/api/academic':     { target: 'http://localhost:8003', changeOrigin: true, rewrite: p => p.replace('/api/academic', '/api/v1') },
      '/api/tutoring':     { target: 'http://localhost:8004', changeOrigin: true, rewrite: p => p.replace('/api/tutoring', '/api/v1') },
      '/api/ti':           { target: 'http://localhost:8005', changeOrigin: true, rewrite: p => p.replace('/api/ti', '/api/v1') },
      '/api/sessions':     { target: 'http://localhost:8006', changeOrigin: true, rewrite: p => p.replace('/api/sessions', '/api/v1') },
      '/api/evaluations':  { target: 'http://localhost:8007', changeOrigin: true, rewrite: p => p.replace('/api/evaluations', '/api/v1') },
      '/api/notifications':{ target: 'http://localhost:8010', changeOrigin: true, rewrite: p => p.replace('/api/notifications', '/api/v1') },
      '/api/reports':      { target: 'http://localhost:8011', changeOrigin: true, rewrite: p => p.replace('/api/reports', '/api/v1') },
    }
  }
})
