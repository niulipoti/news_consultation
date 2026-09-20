import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // 后端地址：默认本机 8000 端口，可用 .env.local 里的 VITE_PROXY_TARGET 覆盖
  const target = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [vue()],
    server: {
      port: 5173,
      // 开发环境把 /api 请求转发给 FastAPI，前端代码里就可以只写相对路径，
      // 既避免了跨域问题，也不用把后端地址硬编码在代码里。
      proxy: {
        '/api': {
          target,
          changeOrigin: true,
          // SSE（AI 流式对话）必须关闭缓冲，否则会「一次性吐出全部内容」
          configure: (proxy) => {
            proxy.on('proxyRes', (proxyRes) => {
              if (proxyRes.headers['content-type']?.includes('text/event-stream')) {
                delete proxyRes.headers['content-length']
              }
            })
          },
        },
        '/health': {
          target,
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      // 生产环境不输出 sourcemap，减小体积
      sourcemap: false,
      chunkSizeWarningLimit: 1500,
    },
  }
})
