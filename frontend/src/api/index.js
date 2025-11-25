import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'
import Cookies from 'js-cookie'

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  },
  // 修复参数序列化问题
  paramsSerializer: (params) => {
    const searchParams = new URLSearchParams()
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined) {
        searchParams.append(key, params[key])
      }
    })
    return searchParams.toString()
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加token到请求头
    const token = Cookies.get('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 如果是表单数据，设置正确的Content-Type
    if (config.data instanceof FormData) {
      config.headers['Content-Type'] = 'multipart/form-data'
    } else if (config.method === 'post' && config.url.includes('/auth/login')) {
      config.headers['Content-Type'] = 'application/x-www-form-urlencoded'
    }
    
    return config
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  async (error) => {
    const { response } = error
    
    if (response) {
      const { status, data } = response
      
      switch (status) {
        case 401:
          const authStore = useAuthStore()
          authStore.logout({ silent: true })
          if (!window.__AUTH_EXPIRED_NOTIFIED) {
            window.__AUTH_EXPIRED_NOTIFIED = true
            if (router.currentRoute.value.path !== '/login') {
              ElMessage.error('登录已过期，请重新登录')
              router.push('/login')
            }
          }
          break
          
        case 403:
          ElMessage.error('没有权限访问该资源')
          break
          
        case 404:
          ElMessage.error('请求的资源不存在')
          break
          
        case 422:
          // 表单验证错误
          if (data.detail && Array.isArray(data.detail)) {
            const errors = data.detail.map(item => item.msg).join(', ')
            ElMessage.error(`参数错误: ${errors}`)
          } else {
            ElMessage.error(data.message || '参数验证失败')
          }
          break
          
        case 500:
          ElMessage.error('服务器内部错误，请稍后重试')
          break
          
        default:
          const errorMessage = data?.error?.message || data?.message || '请求失败'
          ElMessage.error(errorMessage)
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络连接')
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

// 通用请求方法
export const request = {
  get: (url, config = {}) => api.get(url, config),
  post: (url, data = {}) => api.post(url, data),
  put: (url, data = {}) => api.put(url, data),
  delete: (url) => api.delete(url),
  patch: (url, data = {}) => api.patch(url, data)
}

export default api

// 导出各个模块的API
export * from './auth'
export * from './jd'
export * from './resume'
export * from './exam'
export * from './knowledgeBase'
export * from './hrWorkflows'
export * from './admin'