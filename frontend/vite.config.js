import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(async ({ mode }) => {
  const config = {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    server: {
      fs: {
        allow: [path.resolve(__dirname, '..')],
      },
    },
  }

  const frappeui = await importFrappeUIPlugin()
  config.plugins.unshift(
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      buildConfig: {
        indexHtmlPath: '../pathways/www/pathways.html',
        emptyOutDir: true,
        sourcemap: false,
      },
    }),
  )

  return config
})

async function importFrappeUIPlugin() {
  const module = await import('frappe-ui/vite')
  return module.default
}
