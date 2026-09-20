import { defineStore } from 'pinia'
import http from '../../config/http'
import { useUserStore } from '../user'

// 把后端返回的收藏记录统一成页面需要的字段
const normalize = (item) => ({
  ...item,
  // 页面展示用的是 favoriteTime，后端返回的别名也是 favoriteTime，
  // 这里做一次兜底，兼容旧缓存或本地数据
  favoriteTime: item.favoriteTime || item.favorite_time || '',
})

export const useFavoriteStore = defineStore('favorite', {
  state: () => ({
    favorites: [],
    loading: false,
  }),

  getters: {
    getFavorites: (state) => state.favorites,
    isFavorite: (state) => (id) => state.favorites.some((item) => item.id === id),
  },

  actions: {
    // 检查文章收藏状态 - API请求
    async checkFavoriteStatusApi(newsId) {
      const userStore = useUserStore()

      if (!userStore.getLoginStatus) {
        return { success: true, isFavorite: this.isFavorite(newsId), isLocal: true }
      }

      try {
        this.loading = true
        const response = await http.get('/api/favorite/check', {
          params: { newsId },
        })

        if (response && response.code === 200) {
          return { success: true, isFavorite: response.data.isFavorite }
        }
        return { success: false, message: response?.message || '获取收藏状态失败' }
      } catch (error) {
        console.error('检查收藏状态请求失败:', error)
        // 接口异常时回退到本地状态，保证按钮可用
        return { success: true, isFavorite: this.isFavorite(newsId), isLocal: true }
      } finally {
        this.loading = false
      }
    },

    // 添加收藏 - API请求
    async addFavoriteApi(newsId) {
      const userStore = useUserStore()

      if (!userStore.getLoginStatus) {
        return { success: false, message: '请先登录' }
      }

      try {
        this.loading = true
        const response = await http.post('/api/favorite/add', { newsId })

        if (response && response.code === 200) {
          return { success: true, data: response.data }
        }
        return { success: false, message: response?.message || '收藏失败' }
      } catch (error) {
        console.error('添加收藏请求失败:', error)
        return { success: false, message: error.friendlyMessage || '网络请求失败' }
      } finally {
        this.loading = false
      }
    },

    // 取消收藏 - API请求
    async removeFavoriteApi(newsId) {
      const userStore = useUserStore()

      if (!userStore.getLoginStatus) {
        return { success: false, message: '请先登录' }
      }

      try {
        this.loading = true
        const response = await http.delete('/api/favorite/remove', {
          params: { newsId },
        })

        if (response && response.code === 200) {
          return { success: true }
        }
        return { success: false, message: response?.message || '取消收藏失败' }
      } catch (error) {
        console.error('取消收藏请求失败:', error)
        return { success: false, message: error.friendlyMessage || '网络请求失败' }
      } finally {
        this.loading = false
      }
    },

    // 添加收藏 - 本地
    addFavorite(news) {
      if (!this.isFavorite(news.id)) {
        this.favorites.unshift({
          ...news,
          favoriteTime: new Date().toLocaleString(),
        })
        this.saveFavorites()
      }
    },

    // 取消收藏 - 本地
    removeFavorite(id) {
      this.favorites = this.favorites.filter((item) => item.id !== id)
      this.saveFavorites()
    },

    // 切换收藏状态 - 结合API和本地
    async toggleFavorite(news) {
      if (!news || !news.id) {
        console.error('无效的新闻对象:', news)
        return null
      }

      if (this.isFavorite(news.id)) {
        const result = await this.removeFavoriteApi(news.id)
        if (result.success) {
          this.removeFavorite(news.id)
          return false
        }
        return null // 返回null表示操作失败
      }

      const result = await this.addFavoriteApi(news.id)
      if (result.success) {
        this.addFavorite(news)
        return true
      }
      return null // 返回null表示操作失败
    },

    // 清空收藏（本地）
    clearFavorites() {
      this.favorites = []
      this.saveFavorites()
    },

    // 清空收藏 - API请求
    async clearFavoritesApi() {
      const userStore = useUserStore()

      if (!userStore.getLoginStatus) {
        return { success: false, message: '请先登录' }
      }

      try {
        this.loading = true
        const response = await http.delete('/api/favorite/clear')

        if (response && response.code === 200) {
          this.clearFavorites()
          return { success: true }
        }
        return { success: false, message: response?.message || '清空收藏失败' }
      } catch (error) {
        console.error('清空收藏请求失败:', error)
        return { success: false, message: error.friendlyMessage || '网络请求失败' }
      } finally {
        this.loading = false
      }
    },

    // 保存到本地存储
    saveFavorites() {
      localStorage.setItem('news_favorites', JSON.stringify(this.favorites))
    },

    // 从本地存储加载
    loadFavorites() {
      const savedFavorites = localStorage.getItem('news_favorites')
      if (savedFavorites) {
        try {
          this.favorites = JSON.parse(savedFavorites)
        } catch (e) {
          this.favorites = []
        }
      }
    },

    // 获取收藏列表 - API请求
    async getFavoriteListApi(page = 1, pageSize = 10) {
      const userStore = useUserStore()

      if (!userStore.getLoginStatus) {
        return { success: false, message: '请先登录' }
      }

      try {
        this.loading = true
        const response = await http.get('/api/favorite/list', {
          params: { page, pageSize },
        })

        if (response && response.code === 200) {
          this.favorites = (response.data?.list || []).map(normalize)
          return { success: true, data: response.data }
        }
        return { success: false, message: response?.message || '获取收藏列表失败' }
      } catch (error) {
        console.error('获取收藏列表请求失败:', error)
        return { success: false, message: error.friendlyMessage || '网络请求失败' }
      } finally {
        this.loading = false
      }
    },
  },
})
