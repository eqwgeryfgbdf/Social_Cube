import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  root: path.resolve(__dirname, 'static/js'),
  base: '/static/',
  build: {
    outDir: path.resolve(__dirname, 'static/dist'),
    assetsDir: '',
    manifest: true,
    rollupOptions: {
      input: path.resolve(__dirname, 'static/js/index.jsx')
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'static/js')
    }
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'i18next', 'react-i18next']
  },
  publicDir: path.resolve(__dirname, 'static'),
  server: {
    origin: 'http://127.0.0.1:8000'
  }
}); 