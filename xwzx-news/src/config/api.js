/**
 * API 配置文件
 *
 * 重要变更：AI 对话不再由前端直连大模型服务商。
 * 之前前端把 API Key 写在这个文件里，任何人打开浏览器都能拿到密钥，
 * 一旦推到 GitHub 就等于公开泄露。
 * 现在所有 AI 请求都先发到自己的后端（/api/AIchat/...），
 * 由后端读取 .env 中的密钥再去调用 DeepSeek。
 */

// API 基础地址：
//  - 留空 = 使用当前站点（开发时由 vite.config.js 的 proxy 转发到后端）
//  - 也可以在 .env.local 里设置 VITE_API_BASE_URL 指向独立的后端域名
export const apiConfig = {
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  // 普通接口超时时间（毫秒）
  timeout: 15000,
}

// AI 对话相关配置（只包含路径，不含任何密钥）
export const aiChatConfig = {
  // 流式对话接口（推荐，逐字输出）
  streamEndpoint: '/api/AIchat/chat/stream',
  // 一次性返回的对话接口
  chatEndpoint: '/api/AIchat/chat',
  // 查询 AI 服务是否可用
  configEndpoint: '/api/AIchat/config',
}

export default apiConfig
