import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

function spaFallbackPlugin() {
  return {
    name: 'spa-fallback-plugin',
    configureServer(server: any) {
      server.middlewares.use((req: any, res: any, next: any) => {
        try {
          const url: string = req.url || ''
          // Skip vite internal and asset requests
          if (
            url.startsWith('/@') ||
            url.startsWith('/src/') ||
            url.startsWith('/node_modules/') ||
            url.includes('.') // likely a file
          ) {
            return next()
          }
          req.url = '/index.html'
          return next()
        } catch (err) {
          return next()
        }
      })
    }
  }
}

export default defineConfig({
  plugins: [react(), spaFallbackPlugin()],
  server: {
    port: 5173
  }
})
