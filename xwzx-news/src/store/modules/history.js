import { defineStore } from 'pinia'
import http from '../../config/http'
import { useUserStore } from '../user'

// 把后端返回的浏览记录统一成页面需要的字段
const normalize = (item) => ({
  ...item,
  // 页面展示用的是 viewTime，后端返回的是 historyView，这里统一一下
  viewTime: item.historyView || item.viewTime || '',
})

export const useHistoryStore = defineStore('history', {
  state: () => ({
    history: [],
  }),

  getters: {
    getHistory: (state) => state.history,
  },

  actions: {
    // 添加浏览历史 - API请求
    async addHistoryApi(newsId) {
      const userStore = useUserStore()

      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        return { success: false, message: '请先登录' }
      }

      try {
        const response = await http.post('/api/history/add', { newsId })

        if (response && response.code === 200) {
          return { success: true, data: response.data }
        }
        return { success: false, message: response?.message || '添加浏览历史失败' }
      } catch (error) {
        console.error('添加浏览历史请求失败:', error)
        return { success: false, message: error.friendlyMessage || '网络请求失败' }
      }
    },

    // 添加浏览历史 - 本地
    addHistory(news) {
      // 检查是否已存在相同ID的新闻
      const existingIndex = this.history.findIndex((item) => item.id === news.id)

      // 如果已存在，先删除旧记录
      if (existingIndex !== -1) {
        this.history.splice(existingIndex, 1)
      }

      // 添加到历史记录的最前面（最新浏览的在最前面）
      this.history.unshift({
        ...news,
        viewTime: new Date().toLocaleString(),
      })

      // 限制历史记录数量，最多保存50条
      if (this.history.length > 50) {
        this.history.pop()
      }

      this.saveHistory()
    },

    // 清空浏览历史（本地）
    clearHistory() {
      this.history = []
      this.saveHistory()
    },

    // 清空浏览历史 - API请求
    async clearHistoryApi() {
      const userStore = useUserStore()

      if (!userStore.getLoginStatus) {
        this.clearHistory()
        return { success: true, isLocal: true }
      }

      try {
        const response = await http.delete('/api/history/clear')

        if (response && response.code === 200) {
          this.clearHistory()
          return { success: true }
        }
        return { success: false, message: response?.message || '清空浏览历史失败' }
      } catch (error) {
        console.error('清空浏览历史请求异常', error)
        return { success: false, message: error.friendlyMessage || '网络请求失败' }
      }
    },

    // 删除单条浏览历史（本地）
    removeHistory(id) {
      this.history = this.history.filter((item) => (item.historyId ?? item.id) !== id)
      this.saveHistory()
    },

    // 删除单条浏览历史 - API请求
    async removeHistoryApi(id) {
      const userStore = useUserStore()

      if (!userStore.getLoginStatus) {
        this.removeHistory(id)
        return { success: true, isLocal: true }
      }

      try {
        const response = await http.delete(`/api/history/delete/${id}`)

        if (response && response.code === 200) {
          this.removeHistory(id)
          return { success: true }
        }
        return { success: false, message: response?.message || '删除浏览历史失败' }
      } catch (error) {
        console.error('删除浏览历史请求异常', error)
        return { success: false, message: error.friendlyMessage || '网络请求失败' }
      }
    },

    // 保存到本地存储
    saveHistory() {
      localStorage.setItem('news_history', JSON.stringify(this.history))
    },

    // 从本地存储加载
    loadHistory() {
      const savedHistory = localStorage.getItem('news_history')
      if (savedHistory) {
        try {
          this.history = JSON.parse(savedHistory)
        } catch (e) {
          this.history = []
        }
      }
    },

    // 获取浏览历史 - API请求
    async getHistoryListApi() {
      const userStore = useUserStore()

      if (!userStore.getLoginStatus) {
        return { success: false, message: '请先登录', isLocal: true }
      }

      try {
        const response = await http.get('/api/history/list')

        if (response && response.code === 200) {
          const historyList = (response.data?.list || []).map(normalize)
          this.history = historyList
          this.saveHistory()
          return { success: true, data: historyList }
        }
        return { success: false, message: response?.message || '获取浏览历史失败' }
      } catch (error) {
        console.error('获取浏览历史请求异常', error)
        return { success: false, message: error.friendlyMessage || '网络请求失败' }
      }
    },
  },
})
