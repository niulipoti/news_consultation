import { defineStore } from 'pinia'
import http from '../config/http'

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null,
    token: '',
    isLogin: false,
    userBio: '这是我的个人简介',
  }),

  getters: {
    getUserInfo: (state) => state.userInfo,
    getToken: (state) => state.token,
    getLoginStatus: (state) => state.isLogin,
    getUserBio: (state) => state.userInfo?.bio || state.userBio,
  },

  actions: {
    // 把登录结果写入 state，同时把 token 存到 localStorage 供 axios 拦截器使用
    setAuth(data) {
      this.userInfo = data.userInfo
      this.token = data.token
      this.isLogin = true
      localStorage.setItem('user-token', data.token)
    },

    async login(userData) {
      try {
        const response = await http.post('/api/user/login', {
          username: userData.username,
          password: userData.password,
        })

        if (response && response.code === 200) {
          this.setAuth(response.data)
          return { success: true, message: '登录成功' }
        }
        return { success: false, message: response?.message || '登录失败' }
      } catch (error) {
        return {
          success: false,
          message: error.friendlyMessage || '登录请求失败，请稍后再试',
        }
      }
    },

    async register(userData) {
      try {
        const response = await http.post('/api/user/register', {
          username: userData.username,
          password: userData.password,
        })

        if (response && response.code === 200) {
          this.setAuth(response.data)
          return { success: true, message: '注册成功' }
        }
        return { success: false, message: response?.message || '注册失败' }
      } catch (error) {
        return {
          success: false,
          message: error.friendlyMessage || '注册请求失败，请稍后再试',
        }
      }
    },

    async logout() {
      try {
        if (this.token) {
          await http.post('/api/user/logout')
        }
      } catch (error) {
        // 退出登录失败不影响本地清理
      }
      this.userInfo = null
      this.token = ''
      this.isLogin = false
      localStorage.removeItem('user-token')
    },

    // 获取用户信息
    async getUserInfoDetail() {
      if (!this.token) {
        return { success: false, message: '未登录' }
      }

      try {
        const response = await http.get('/api/user/info')
        if (response && response.code === 200) {
          this.userInfo = response.data
          return { success: true, message: '获取用户信息成功', data: response.data }
        }
        return { success: false, message: response?.message || '获取用户信息失败' }
      } catch (error) {
        // 令牌失效时自动登出，避免界面卡在「已登录」状态
        if (error.response?.status === 401) {
          this.logout()
        }
        return {
          success: false,
          message: error.friendlyMessage || '获取用户信息失败，请稍后再试',
        }
      }
    },

    // 更新个人资料（不仅是简介，nickname / avatar / gender 都能改）
    async updateUserProfile(payload) {
      if (!this.token) {
        return { success: false, message: '未登录' }
      }

      try {
        const response = await http.put('/api/user/update', payload)
        if (response && response.code === 200) {
          this.userInfo = { ...this.userInfo, ...response.data }
          return { success: true, message: '修改成功', data: response.data }
        }
        return { success: false, message: response?.message || '修改失败' }
      } catch (error) {
        return {
          success: false,
          message: error.friendlyMessage || '修改失败，请稍后再试',
        }
      }
    },

    // 兼容旧调用：只更新个人简介
    async updateUserBio(bio) {
      return this.updateUserProfile({ bio })
    },

    // 修改密码
    async updatePassword(oldPassword, newPassword) {
      if (!this.token) {
        return { success: false, message: '未登录' }
      }

      try {
        const response = await http.put('/api/user/password', {
          oldPassword,
          newPassword,
        })
        if (response && response.code === 200) {
          return { success: true, message: '密码修改成功' }
        }
        return { success: false, message: response?.message || '密码修改失败' }
      } catch (error) {
        return {
          success: false,
          message: error.friendlyMessage || '密码修改失败，请稍后再试',
        }
      }
    },
  },

  // 只持久化必要的字段，避免把整个 store 写进 localStorage
  persist: {
    key: 'user-store',
    pick: ['userInfo', 'token', 'isLogin'],
  },
})
