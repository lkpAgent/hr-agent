import { request } from '@/api'

export const adminApi = {
  listUsers(params = {}) {
    return request.get('/users/', { params })
  },
  createUser(data) {
    return request.post('/users/admin/users', data)
  },
  listRoles() {
    return request.get('/users/admin/roles')
  },
  createRole(data) {
    return request.post('/users/admin/roles', data)
  },
  deleteRole(roleId) {
    return request.delete(`/users/admin/roles/${roleId}`)
  },
  getUserRoles(userId) {
    return request.get(`/users/admin/users/${userId}/roles`)
  },
  assignUserRoles(userId, roleIds) {
    return request.put(`/users/admin/users/${userId}/roles`, { role_ids: roleIds })
  }
}

export const accountApi = {
  getMyRoles() {
    return request.get('/users/me/roles')
  }
}
