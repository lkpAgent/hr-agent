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

  // 解析自然语言需求为结构化表单字段
  parseRequirements(data) {
    return request.post('/hr-workflows/parse-requirements', data)
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

  // 根据简历ID生成面试方案
  generateInterviewPlanByResume(data) {
    if (data.stream) {
      const token = Cookies.get('token')
      const formData = new FormData()
      formData.append('resume_id', data.resume_id)
      if (data.conversation_id) {
        formData.append('conversation_id', data.conversation_id)
      }
      formData.append('stream', data.stream)

      return fetch(`/api/v1/hr-workflows/generate-interview-plan-by-resume`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })
    }
    
    return request.post('/hr-workflows/generate-interview-plan-by-resume', data)
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
  },

  // 生成评分标准
  generateScoringCriteria(data) {
    if (data.stream) {
      const token = Cookies.get('token')
      return fetch(`/api/v1/hr-workflows/generate-scoring-criteria`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      })
    }
    
    return request.post('/hr-workflows/generate-scoring-criteria', data)
  },

  // 保存评分标准
  createScoringCriteria(data) {
    return request.post('/hr-workflows/scoring-criteria/save', data)
  },

  // 更新评分标准
  updateScoringCriteria(id, data) {
    return request.put(`/hr-workflows/scoring-criteria/${id}`, data)
  },

  // 获取评分标准详情
  getScoringCriteria(id) {
    return request.get(`/hr-workflows/scoring-criteria/${id}`)
  },

  // 获取评分标准列表
  getScoringCriteriaList(params) {
    return request.get('/hr-workflows/scoring-criteria', { params })
  },

  // 根据JD ID获取评分标准
  getScoringCriteriaByJD(jdId) {
    console.log('API调用 getScoringCriteriaByJD，参数:', { job_description_id: jdId })
    return request.get('/hr-workflows/scoring-criteria', { 
      params: { job_description_id: jdId } 
    })
  },

  // 面试方案相关API
  // 保存面试方案内容
  saveInterviewPlan(planId, data) {
    return request.post(`/interview-plans/${planId}/save`, data)
  },

  // 创建面试方案
  createInterviewPlan(data) {
    return request.post('/interview-plans', data)
  },

  // 更新面试方案
  updateInterviewPlan(planId, data) {
    return request.put(`/interview-plans/${planId}`, data)
  },

  // 获取面试方案详情
  getInterviewPlan(planId) {
    return request.get(`/interview-plans/${planId}`)
  },

  // 获取面试方案列表
  getInterviewPlanList(params) {
    return request.get('/interview-plans/', { params })
  },

  // 保存生成的面试方案
  saveGeneratedInterviewPlan(data) {
    return request.post('/interview-plans/save-generated', data)
  },

  // 删除面试方案
  deleteInterviewPlan(planId) {
    return request.delete(`/interview-plans/${planId}`)
  }
}