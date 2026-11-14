import path from 'path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'

export default defineConfig({
  plugins: [
    frappeui({
      frontendRoute: '/petrodesk',
      frappeProxy: { port: 8087 },
      buildConfig: {
        outDir: path.resolve(__dirname, '../petrodiesel/public/frontend'),
        indexHtmlPath: path.resolve(__dirname, '../petrodiesel/www/petrodesk.html'),
        baseUrl: '/assets/petrodiesel/frontend/',
      },
    }),
    vue(),
  ],
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
  optimizeDeps: { include: ['frappe-ui > feather-icons', 'showdown', 'engine.io-client'] },
})
