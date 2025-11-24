import { request } from './index'

// 获取用户的对话列表
export function getConversations(params = {}) {
  return request.get('/conversations/', {
    params: {
      skip: params.skip || 0,
      limit: params.limit || 100,
      ...params
    }
  })
}

// 创建新对话
export function createConversation(data) {
  return request.post('/conversations/', data)
}

// 获取单个对话详情
export function getConversation(conversationId) {
  return request.get(`/conversations/${conversationId}`)
}

// 更新对话
export function updateConversation(conversationId, data) {
  return request.put(`/conversations/${conversationId}`, data)
}

// 删除对话
export function deleteConversation(conversationId) {
  return request.delete(`/conversations/${conversationId}`)
}

// 获取对话的消息列表
export function getConversationMessages(conversationId, params = {}) {
  return request.get(`/conversations/${conversationId}/messages`, {
    params: {
      skip: params.skip || 0,
      limit: params.limit || 100,
      ...params
    }
  })
}

// 保存对话消息（批量保存）
export function saveConversationMessages(conversationId, messages) {
  return request.post(`/conversations/${conversationId}/messages/batch`, {
    messages: messages
  })
}