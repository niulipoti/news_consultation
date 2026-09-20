import { defineStore } from 'pinia'
import http from '../../config/http'

export const useNewsStore = defineStore('news', {
  state: () => ({
    newsList: [],
    newsDetail: {},
    categories: [],
    currentCategory: null,
    loading: false,
    refreshing: false,
    finished: false,
    categoriesLoading: false,
  }),

  actions: {
    // 获取新闻分类
    async getCategories() {
      if (this.categoriesLoading) return

      this.categoriesLoading = true

      try {
        const response = await http.get('/api/news/categories')
        if (response && response.code === 200) {
          // 后端已经按要求排好序，这里原样使用
          this.categories = response.data || []
          if (!this.currentCategory && this.categories.length > 0) {
            this.currentCategory = this.categories[0].id
          }
        }
      } catch (error) {
        console.error('获取新闻分类失败:', error)
        // 接口失败时的兜底分类，保证界面不会空白
        this.categories = [
          { id: 1, name: '头条' },
          { id: 2, name: '社会' },
          { id: 3, name: '国内' },
          { id: 4, name: '国际' },
          { id: 5, name: '娱乐' },
          { id: 6, name: '体育' },
          { id: 7, name: '科技' },
        ]
        if (!this.currentCategory) {
          this.currentCategory = this.categories[0].id
        }
      } finally {
        this.categoriesLoading = false
      }
    },

    // 切换新闻分类：清空列表并重新拉第一页
    changeCategory(categoryId) {
      if (this.currentCategory === categoryId) return
      this.currentCategory = categoryId
      this.newsList = []
      this.finished = false
      this.getNewsList(true)
    },

    // 获取新闻列表
    async getNewsList(isRefresh = false) {
      if (this.finished && !isRefresh) return

      if (isRefresh) {
        this.refreshing = true
        this.newsList = []
        this.finished = false
      }

      this.loading = true

      try {
        const params = {
          categoryId: this.currentCategory,
          // 下拉刷新永远取第 1 页；加载更多按已有条数推算下一页
          page: isRefresh ? 1 : Math.floor(this.newsList.length / 10) + 1,
          pageSize: 10,
        }

        const response = await http.get('/api/news/list', { params })

        if (response && response.code === 200) {
          const data = response.data || {}
          const newsData = data.list || []

          this.newsList = isRefresh ? newsData : [...this.newsList, ...newsData]

          // 后端直接给出是否还有更多，比前端靠条数猜更准确
          this.finished = !data.hasMore
        } else {
          this.finished = true
        }
      } catch (error) {
        console.error('获取新闻列表失败:', error)
        // 请求失败时结束加载状态，避免列表一直转圈
        this.finished = true
      } finally {
        this.loading = false
        this.refreshing = false
      }
    },

    // 获取新闻详情
    async getNewsDetail(id) {
      try {
        const response = await http.get('/api/news/detail', { params: { id } })

        if (response && response.code === 200) {
          this.newsDetail = response.data
          return { success: true, data: response.data }
        }
        this.newsDetail = {}
        return { success: false, message: response?.message || '获取新闻详情失败' }
      } catch (error) {
        console.error('获取新闻详情失败:', error)
        this.newsDetail = {}
        return { success: false, message: error.friendlyMessage || '获取新闻详情失败' }
      }
    },

    // 获取分类名称
    getCategoryName(categoryId) {
      const category = this.categories.find((item) => item.id === categoryId)
      return category ? category.name : '未知'
    },
  },
})
