import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '../', '')

  const frontendPort = parseInt(env.VITE_FRONTEND_PORT) || 3000
  const backendPort = parseInt(env.VITE_BACKEND_PORT) || 8000
  const backendHost = env.VITE_BACKEND_HOST || 'localhost'

  return {
    plugins: [react()],
    server: {
      port: frontendPort,
      open: true,
      proxy: {
        '/api': {
          target: `http://${backendHost}:${backendPort}`,
          changeOrigin: true,
        }
      }
    },
    build: {
      outDir: 'dist',
      sourcemap: env.VITE_NODE_ENV === 'development'
    },
    define: {
      __APP_VERSION__: JSON.stringify(env.VITE_APP_VERSION),
      __APP_NAME__: JSON.stringify(env.VITE_APP_NAME),
    }
  }
})