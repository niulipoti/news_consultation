import axios from 'axios'
import { apiConfig } from './api'

/**
 * 统一的 axios 实例。
 *
 * 以前每个 store 各自 import axios 并手写 `${apiConfig.baseURL}/api/...`，
 * 导致：后端地址写错要改好几处、没有统一超时、token 要手动往 headers 里塞。
 * 这里统一收口。
 *
 * 约定：响应拦截器直接把后端的 { code, message, data } 返回给调用方，
 * 业务代码只需判断 `code === 200`（失败会走 catch）。
 */
const http = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: apiConfig.timeout,
})

// 读取登录令牌：优先用专门的 key，取不到时再从持久化的 user-store 里兜底
function readToken() {
  const direct = localStorage.getItem('user-token')
  if (direct) return direct

  try {
    const persisted = JSON.parse(localStorage.getItem('user-store') || '{}')
    return persisted.token || ''
  } catch (e) {
    return ''
  }
}

// 请求拦截器：自动携带登录令牌
http.interceptors.request.use((config) => {
  const token = readToken()
  if (token) {
    config.headers = config.headers || {}
    // 后端同时兼容 "Bearer xxx" 和 "xxx" 两种写法
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一处理错误
http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // HTTP 状态码非 2xx 时，FastAPI 会把错误放在 detail 里
    const body = error.response?.data
    const message =
      body?.message ||
      body?.detail ||
      (error.code === 'ECONNABORTED'
        ? '请求超时，请稍后重试'
        : '网络异常，请确认后端服务已启动')
    error.friendlyMessage = message
    return Promise.reject(error)
  },
)

export default http
