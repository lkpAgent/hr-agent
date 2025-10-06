import { request } from '@/api/index'
import Cookies from 'js-cookie'

export const hrWorkflowsApi = {
  // 获取工作流类型列表
  getWorkflowTypes() {
    return request.get('/hr-workflows/types')
  },

  // 生成JD
  generateJD(data) {
    if (data.stream) {
      const token = Cookies.get('token')
      return fetch(`/api/v1/hr-workflows/generate-jd`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      })
    }
    
    return request.post('/hr-workflows/generate-jd', data)
  },

  // 简历评价
  evaluateResume(data) {
    if (data.stream) {
      const token = Cookies.get('token')
      return fetch(`/api/v1/hr-workflows/evaluate-resume`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      })
    }
    
    return request.post('/hr-workflows/evaluate-resume', data)
  },

  // 生成面试方案
  generateInterviewPlan(data) {
    if (data.stream) {
      const token = Cookies.get('token')
      return fetch(`/api/v1/hr-workflows/generate-interview-plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      })
    }
    
    return request.post('/hr-workflows/generate-interview-plan', data)
  },

  // 调用自定义工作流
  callCustomWorkflow(data) {
    if (data.stream) {
      const token = Cookies.get('token')
      return fetch(`/api/v1/hr-workflows/custom`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      })
    }
    
    return request.post('/hr-workflows/custom', data)
  },

  // 保存JD
  saveJD(data) {
    return request.post('/hr-workflows/jd/save', data)
  },

  // 更新JD
  updateJD(id, data) {
    return request.put(`/hr-workflows/jd/${id}`, data)
  },

  // 获取JD详情
  getJD(id) {
    return request.get(`/hr-workflows/jd/${id}`)
  },

  // 获取JD列表
  getJDList(params = {}) {
    // 手动构建查询字符串
    const searchParams = new URLSearchParams()
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined) {
        searchParams.append(key, params[key])
      }
    })
    const queryString = searchParams.toString()
    const url = queryString ? `/hr-workflows/jd?${queryString}` : '/hr-workflows/jd'
    return request.get(url)
  },

  // 删除JD
  deleteJD(id) {
    return request.delete(`/hr-workflows/jd/${id}`)
  }
}