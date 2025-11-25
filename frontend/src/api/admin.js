import request from '@/utils/request'

// 用户管理相关API
export const userApi = {
  // 获取用户列表
  getUserList(params) {
    const p = { ...(params || {}) }
    if (p.page && p.size) {
      p.skip = (Number(p.page) - 1) * Number(p.size)
      p.limit = Number(p.size)
      delete p.page
      delete p.size
    }
    return request({
      url: '/users/',
      method: 'get',
      params: p
    })
  },

  // 获取单个用户详情
  getUser(id) {
    return request({
      url: `/users/${id}`,
      method: 'get'
    })
  },

  getUserRoles(id) {
    return request({
      url: `/users/${id}/roles`,
      method: 'get'
    })
  },

  // 创建用户
  createUser(data) {
    return request({
      url: '/users/',
      method: 'post',
      data
    })
  },

  // 更新用户
  updateUser(id, data) {
    return request({
      url: `/users/${id}`,
      method: 'put',
      data
    })
  },

  // 删除用户
  deleteUser(id) {
    return request({
      url: `/users/${id}`,
      method: 'delete'
    })
  },

  // 更新用户状态
  updateUserStatus(id, status) {
    return request({
      url: `/users/${id}/status`,
      method: 'patch',
      data: { status }
    })
  },

  // 重置用户密码
  resetUserPassword(id, password) {
    return request({
      url: `/users/${id}/reset-password`,
      method: 'post',
      data: { password }
    })
  }
}

// 角色管理相关API
export const roleApi = {
  // 获取角色列表
  getRoleList(params) {
    const p = { ...(params || {}) }
    if (p.page && p.size) {
      p.skip = (Number(p.page) - 1) * Number(p.size)
      p.limit = Number(p.size)
      delete p.page
      delete p.size
    }
    return request({
      url: '/roles/',
      method: 'get',
      params: p
    })
  },

  // 获取单个角色详情
  getRole(id) {
    return request({
      url: `/roles/${id}`,
      method: 'get'
    })
  },

  // 创建角色
  createRole(data) {
    return request({
      url: '/roles/',
      method: 'post',
      data
    })
  },

  // 更新角色
  updateRole(id, data) {
    return request({
      url: `/roles/${id}`,
      method: 'put',
      data
    })
  },

  // 删除角色
  deleteRole(id) {
    return request({
      url: `/roles/${id}`,
      method: 'delete'
    })
  }
}

// 权限管理相关API
export const permissionApi = {
  // 获取权限列表
  getPermissionList(params) {
    return request({
      url: '/permissions/',
      method: 'get',
      params
    })
  },

  // 获取权限树形结构
  getPermissionTree() {
    return request({
      url: '/permissions/tree',
      method: 'get'
    })
  }
}

// 邮箱配置管理相关API
export const emailConfigApi = {
  // 获取邮箱配置列表
  getEmailConfigList(params) {
    const p = { ...(params || {}) }
    if (p.page && p.size) {
      p.skip = (Number(p.page) - 1) * Number(p.size)
      p.limit = Number(p.size)
      delete p.page
      delete p.size
    }
    return request({
      url: '/email-configs/',
      method: 'get',
      params: p
    })
  },

  // 获取单个邮箱配置详情
  getEmailConfig(id) {
    return request({
      url: `/email-configs/${id}`,
      method: 'get'
    })
  },

  // 创建邮箱配置
  createEmailConfig(data) {
    return request({
      url: '/email-configs/',
      method: 'post',
      data
    })
  },

  // 更新邮箱配置
  updateEmailConfig(id, data) {
    return request({
      url: `/email-configs/${id}`,
      method: 'put',
      data
    })
  },

  // 删除邮箱配置
  deleteEmailConfig(id) {
    return request({
      url: `/email-configs/${id}`,
      method: 'delete'
    })
  },

  // 测试邮箱连接
  testEmailConnection(id, data) {
    return request({
      url: `/email-configs/${id}/test`,
      method: 'post',
      data
    })
  },

  // 手动触发简历抓取
  fetchEmails(id) {
    return request({
      url: `/email-configs/${id}/fetch`,
      method: 'post'
    })
  },

  // 获取邮箱抓取日志
  getEmailFetchLogs(configId, params) {
    return request({
      url: `/email-configs/${configId}/logs`,
      method: 'get',
      params
    })
  }
}

// 系统统计相关API
export const systemApi = {
  // 获取系统统计信息
  getSystemStats() {
    return request({
      url: '/api/v1/system/stats',
      method: 'get'
    })
  },

  // 获取系统最近活动
  getRecentActivity(params) {
    return request({
      url: '/api/v1/system/activity',
      method: 'get',
      params
    })
  },

  // 获取在线用户数
  getOnlineUsers() {
    return request({
      url: '/api/v1/system/online-users',
      method: 'get'
    })
  }
}

export default {
  userApi,
  roleApi,
  permissionApi,
  emailConfigApi,
  systemApi
}
