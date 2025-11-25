<template>
  <div class="user-management" v-loading="loading">
    <div class="page-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><User /></el-icon>
            用户管理
          </h1>
          <p class="page-description">管理系统用户，分配角色权限，控制用户状态</p>
        </div>
        <div class="header-actions">
          <el-button @click="createNewUser" type="primary" size="large">
            <el-icon><Plus /></el-icon>
            新增用户
          </el-button>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <div class="main-content">
        <!-- 左侧用户列表 -->
        <div class="user-list-panel">
          <el-card class="list-card">
            <template #header>
              <div class="list-header">
                <span class="list-title">
                  <el-icon><List /></el-icon>
                  用户列表 ({{ pagination.total }})
                </span>
                <div class="list-actions">
                  <el-input
                    v-model="searchKeyword"
                    placeholder="搜索用户名或邮箱..."
                    clearable
                    size="small"
                    style="width: 100px"
                    @input="handleSearch"
                  >
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                  <el-select
                    v-model="statusFilter"
                    placeholder="状态筛选"
                    size="small"
                    style="width: 120px; margin-left: 10px"
                    @change="handleSearch"
                  >
                    <el-option label="全部状态" value="" />
                    <el-option label="启用" value="active" />
                    <el-option label="禁用" value="disabled" />
                    <el-option label="锁定" value="locked" />
                  </el-select>
                </div>
              </div>
            </template>

            <!-- 用户列表内容 -->
            <div class="user-list-content">
              <div v-if="userListLoading" class="loading-container">
                <el-skeleton :rows="5" animated />
              </div>
              
              <div v-else-if="userList.length === 0" class="empty-container">
                <el-empty description="暂无用户数据" :image-size="120">
                  <el-button type="primary" @click="createNewUser">
                    <el-icon><Plus /></el-icon>
                    创建第一个用户
                  </el-button>
                </el-empty>
              </div>

              <div v-else class="user-items">
                <div
                  v-for="user in userList"
                  :key="user.id"
                  :class="['user-item', { active: selectedUser?.id === user.id }]"
                  @click="selectUser(user)"
                >
                  <div class="user-item-header">
                    <div class="user-info">
                      <el-avatar :size="40" :src="user.avatar_url">
                        <el-icon><User /></el-icon>
                      </el-avatar>
                      <div class="user-details">
                        <h4 class="user-name">{{ user.full_name || user.username }}</h4>
                        <p class="user-email">{{ user.email }}</p>
                      </div>
                    </div>
                    <div class="user-actions">
                      <el-tag :type="getStatusType(computeUserStatus(user))" size="small">
                        {{ getStatusText(computeUserStatus(user)) }}
                      </el-tag>
                      <el-dropdown trigger="click" @command="handleUserAction">
                        <el-button text size="small">
                          <el-icon><MoreFilled /></el-icon>
                        </el-button>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item :command="{ action: 'edit', user }">
                              <el-icon><Edit /></el-icon>
                              编辑
                            </el-dropdown-item>
                            <el-dropdown-item :command="{ action: 'toggle-status', user }">
                              <el-icon><SwitchButton /></el-icon>
                              {{ computeUserStatus(user) === 'active' ? '禁用' : '启用' }}
                            </el-dropdown-item>
                            <el-dropdown-item :command="{ action: 'reset-password', user }" divided>
                              <el-icon><Key /></el-icon>
                              重置密码
                            </el-dropdown-item>
                            <el-dropdown-item :command="{ action: 'delete', user }">
                              <el-icon><Delete /></el-icon>
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                  </div>
                  
                  <div class="user-item-content">
                    <div class="user-meta">
                      <span class="meta-item">
                        <el-icon><Avatar /></el-icon>
                        {{ getRoleName(user.role_id) }}
                      </span>
                      <span class="meta-item">
                        <el-icon><OfficeBuilding /></el-icon>
                        {{ user.department || '未设置' }}
                      </span>
                    </div>
                    <div class="user-time">
                      创建时间: {{ formatDate(user.created_at) }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- 分页 -->
              <div v-if="userList.length > 0" class="pagination-container">
                <el-pagination
                  v-model:current-page="pagination.page"
                  v-model:page-size="pagination.size"
                  :total="pagination.total"
                  :page-sizes="[10, 20, 50]"
                  layout="total, sizes, prev, pager, next"
                  small
                  @size-change="handleSizeChange"
                  @current-change="handlePageChange"
                />
              </div>
            </div>
          </el-card>
        </div>

        <!-- 右侧编辑区域 -->
        <div class="user-editor-panel">
          <!-- 欢迎页面 -->
          <div v-if="!selectedUser && !isCreatingNew" class="welcome-container">
            <el-card class="welcome-card">
              <div class="welcome-content">
                <div class="welcome-icon">
                  <el-icon size="80"><User /></el-icon>
                </div>
                <h2>欢迎使用用户管理</h2>
                <p>选择左侧的用户进行编辑，或创建新用户</p>
                <div class="welcome-actions">
                  <el-button type="primary" @click="createNewUser" size="large">
                    <el-icon><Plus /></el-icon>
                    创建新用户
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>

          <!-- 用户编辑区域 -->
          <div v-else class="user-editor-content">
            <!-- 编辑器头部 -->
            <div class="editor-header">
              <div class="editor-title">
                <h3>{{ isCreatingNew ? '创建新用户' : `编辑用户: ${selectedUser?.full_name || selectedUser?.username}` }}</h3>
                <el-tag v-if="!isCreatingNew" :type="getStatusType(computeUserStatus(selectedUser || {}))" size="small">
                  {{ getStatusText(computeUserStatus(selectedUser || {})) }}
                </el-tag>
              </div>
              <div class="editor-actions">
                <el-button @click="resetUserForm" :disabled="saving">
                  <el-icon><Refresh /></el-icon>
                  重置
                </el-button>
                <el-button type="primary" @click="saveUser" :loading="saving">
                  <el-icon><Check /></el-icon>
                  保存
                </el-button>
              </div>
            </div>

            <!-- 编辑器主要内容 -->
            <div class="editor-main">
              <el-card class="user-form-card">
                <template #header>
                  <div class="card-header">
                    <el-icon><Setting /></el-icon>
                    <span>用户信息</span>
                  </div>
                </template>

                <el-form
                  ref="userFormRef"
                  :model="userForm"
                  :rules="userRules"
                  label-width="100px"
                  label-position="top"
                  class="user-form"
                >
                  <el-row :gutter="16">
                    <el-col :span="12">
                      <el-form-item label="用户名" prop="username">
                        <el-input 
                          v-model="userForm.username" 
                          placeholder="请输入用户名"
                          :disabled="!isCreatingNew"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="12">
                      <el-form-item label="邮箱" prop="email">
                        <el-input 
                          v-model="userForm.email" 
                          placeholder="请输入邮箱地址"
                          :disabled="!isCreatingNew"
                        />
                      </el-form-item>
                    </el-col>
                  </el-row>

                  <el-row :gutter="16">
                    <el-col :span="12">
                      <el-form-item label="姓名" prop="full_name">
                        <el-input v-model="userForm.full_name" placeholder="请输入真实姓名" />
                      </el-form-item>
                    </el-col>
                    <el-col :span="12">
                      <el-form-item label="手机号" prop="phone">
                        <el-input v-model="userForm.phone" placeholder="请输入手机号" />
                      </el-form-item>
                    </el-col>
                  </el-row>

                  <el-row :gutter="16">
                    <el-col :span="12">
                      <el-form-item label="部门" prop="department">
                        <el-input v-model="userForm.department" placeholder="请输入部门名称" />
                      </el-form-item>
                    </el-col>
                    <el-col :span="12">
                      <el-form-item label="用户角色" prop="role_id">
                        <el-select v-model="userForm.role_id" placeholder="请选择角色" style="width: 100%">
                          <el-option
                            v-for="role in roleList"
                            :key="role.id"
                            :label="role.name"
                            :value="role.id"
                          />
                        </el-select>
                      </el-form-item>
                    </el-col>
                  </el-row>

                  <el-row :gutter="16" v-if="isCreatingNew">
                    <el-col :span="12">
                      <el-form-item label="密码" prop="password">
                        <el-input 
                          v-model="userForm.password" 
                          type="password"
                          placeholder="请输入密码"
                          show-password
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="12">
                      <el-form-item label="确认密码" prop="confirmPassword">
                        <el-input 
                          v-model="userForm.confirmPassword" 
                          type="password"
                          placeholder="请再次输入密码"
                          show-password
                        />
                      </el-form-item>
                    </el-col>
                  </el-row>

                  <el-form-item label="用户状态" prop="status">
                    <el-radio-group v-model="userForm.status">
                      <el-radio label="active">启用</el-radio>
                      <el-radio label="disabled">禁用</el-radio>
                      <el-radio label="locked">锁定</el-radio>
                    </el-radio-group>
                  </el-form-item>
                </el-form>
              </el-card>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 重置密码对话框 -->
    <el-dialog
      v-model="resetPasswordDialog.visible"
      title="重置密码"
      width="400px"
    >
      <el-form
        ref="resetPasswordFormRef"
        :model="resetPasswordForm"
        :rules="resetPasswordRules"
        label-width="80px"
      >
        <el-form-item label="新密码" prop="newPassword">
          <el-input 
            v-model="resetPasswordForm.newPassword" 
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input 
            v-model="resetPasswordForm.confirmPassword" 
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPasswordDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="confirmResetPassword" :loading="resetPasswordDialog.loading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  Plus,
  List,
  Search,
  MoreFilled,
  Edit,
  Delete,
  SwitchButton,
  Key,
  Avatar,
  OfficeBuilding,
  Refresh,
  Check,
  Setting
} from '@element-plus/icons-vue'
import { userApi, roleApi } from '@/api/admin'

// 响应式数据
const loading = ref(false)
const userListLoading = ref(false)
const saving = ref(false)

// 用户列表相关
const userList = ref([])
const selectedUser = ref(null)
const isCreatingNew = ref(false)
const searchKeyword = ref('')
const statusFilter = ref('')

// 角色列表
const roleList = ref([])

// 分页数据
const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

// 用户表单
const userFormRef = ref()
const userForm = reactive({
  username: '',
  email: '',
  full_name: '',
  phone: '',
  department: '',
  role_id: '',
  status: 'active',
  password: '',
  confirmPassword: ''
})

// 表单验证规则
const userRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3-20个字符之间', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  full_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  role_id: [
    { required: true, message: '请选择用户角色', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== userForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 重置密码相关
const resetPasswordDialog = reactive({
  visible: false,
  loading: false,
  userId: null
})

const resetPasswordFormRef = ref()
const resetPasswordForm = reactive({
  newPassword: '',
  confirmPassword: ''
})

const resetPasswordRules = {
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== resetPasswordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 计算属性
const getRoleName = (roleId) => {
  const role = roleList.value.find(r => r.id === roleId)
  return role ? role.name : '未知角色'
}

// 方法
const createNewUser = () => {
  isCreatingNew.value = true
  selectedUser.value = null
  resetUserForm()
}

const selectUser = async (user) => {
  selectedUser.value = user
  isCreatingNew.value = false
  
  // 填充表单数据
  userForm.username = user.username
  userForm.email = user.email
  userForm.full_name = user.full_name || ''
  userForm.phone = user.phone || ''
  userForm.department = user.department || ''
  userForm.role_id = await deriveRoleIdFromUser(user) || ''
  userForm.status = user.status || 'active'
  userForm.password = ''
  userForm.confirmPassword = ''
}

const resetUserForm = () => {
  userForm.username = ''
  userForm.email = ''
  userForm.full_name = ''
  userForm.phone = ''
  userForm.department = ''
  // 默认分配普通用户角色
  const defaultRole = roleList.value.find(r => r.name === '普通用户')
  userForm.role_id = defaultRole?.id || ''
  userForm.status = 'active'
  userForm.password = ''
  userForm.confirmPassword = ''
  
  if (userFormRef.value) {
    userFormRef.value.clearValidate()
  }
}

const saveUser = async () => {
  try {
    await userFormRef.value.validate()
    saving.value = true
    
    const userData = {
      username: userForm.username,
      email: userForm.email,
      full_name: userForm.full_name,
      phone: userForm.phone,
      department: userForm.department,
      role_id: userForm.role_id,
      status: userForm.status
    }
    
    if (isCreatingNew.value) {
      userData.password = userForm.password
      // 调用创建用户API
    await userApi.createUser(userData)
    ElMessage.success('用户创建成功')
    } else {
      // 调用更新用户API
    await userApi.updateUser(selectedUser.value.id, userData)
    ElMessage.success('用户更新成功')
    }
    
    await fetchUserList()
  } catch (error) {
    console.error('保存用户失败:', error)
    ElMessage.error('保存用户失败，请重试')
  } finally {
    saving.value = false
  }
}

const handleUserAction = async ({ action, user }) => {
  switch (action) {
    case 'edit':
      selectUser(user)
      break
    case 'toggle-status':
      await toggleUserStatus(user)
      break
    case 'reset-password':
      openResetPasswordDialog(user)
      break
    case 'delete':
      await deleteUser(user)
      break
  }
}

const toggleUserStatus = async (user) => {
  try {
    const newStatus = computeUserStatus(user) === 'active' ? 'disabled' : 'active'
    const actionText = user.status === 'active' ? '禁用' : '启用'
    
    await ElMessageBox.confirm(
      `确定要${actionText}用户"${user.full_name || user.username}"吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 调用更新状态API
    await userApi.updateUserStatus(user.id, newStatus)
    ElMessage.success(`${actionText}用户成功`)
    await fetchUserList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('更新用户状态失败:', error)
      ElMessage.error('更新用户状态失败')
    }
  }
}

const openResetPasswordDialog = (user) => {
  resetPasswordDialog.userId = user.id
  resetPasswordDialog.visible = true
  resetPasswordForm.newPassword = ''
  resetPasswordForm.confirmPassword = ''
}

const confirmResetPassword = async () => {
  try {
    await resetPasswordFormRef.value.validate()
    resetPasswordDialog.loading = true
    
    // 调用重置密码API
    await userApi.resetUserPassword(resetPasswordDialog.userId, resetPasswordForm.newPassword)
    ElMessage.success('密码重置成功')
    resetPasswordDialog.visible = false
  } catch (error) {
    console.error('重置密码失败:', error)
    ElMessage.error('重置密码失败')
  } finally {
    resetPasswordDialog.loading = false
  }
}

const deleteUser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户"${user.full_name || user.username}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 调用删除用户API
    await userApi.deleteUser(user.id)
    ElMessage.success('用户删除成功')
    
    if (selectedUser.value?.id === user.id) {
      selectedUser.value = null
      isCreatingNew.value = false
    }
    
    await fetchUserList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error('删除用户失败')
    }
  }
}

const fetchUserList = async () => {
  try {
    userListLoading.value = true
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    
    // 调用获取用户列表API
    const response = await userApi.getUserList(params)
    if (Array.isArray(response)) {
      userList.value = response
      pagination.total = response.length || 0
    } else {
      userList.value = response.items || []
      pagination.total = response.total || (userList.value.length || 0)
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    userListLoading.value = false
  }
}

const fetchRoleList = async () => {
  try {
    const response = await roleApi.getRoleList({ page: 1, size: 100 })
    roleList.value = Array.isArray(response) ? response : (response.items || [])
  } catch (error) {
    console.error('获取角色列表失败:', error)
    ElMessage.error('获取角色列表失败')
  }
}

// 根据用户信息推断角色并返回对应角色ID
const deriveRoleIdFromUser = async (user) => {
  if (!user) return ''
  try {
    const roles = await userApi.getUserRoles(user.id)
    const list = Array.isArray(roles) ? roles : (roles.items || [])
    if (list.length > 0) {
      const admin = list.find(r => r.name === '超级管理员')
      return (admin?.id || list[0]?.id) || ''
    }
    const normal = roleList.value.find(r => r.name === '普通用户')
    return normal?.id || ''
  } catch (e) {
    const normal = roleList.value.find(r => r.name === '普通用户')
    return normal?.id || ''
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchUserList()
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchUserList()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchUserList()
}

const getStatusType = (status) => {
  const statusMap = {
    'active': 'success',
    'disabled': 'danger',
    'locked': 'warning'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    'active': '启用',
    'disabled': '禁用',
    'locked': '锁定'
  }
  return statusMap[status] || '未知'
}

const computeUserStatus = (user) => {
  return user && user.is_active ? 'active' : 'disabled'
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

// 生命周期
onMounted(async () => {
  await fetchRoleList()
  await fetchUserList()
})
</script>

<style lang="scss" scoped>
.user-management {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
  
  // 添加背景装饰
  &::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
    background-size: 50px 50px;
    animation: float 20s linear infinite;
    pointer-events: none;
  }
  
  .page-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 20px;
    max-width: 95%;
    margin: 0 auto;
    width: 100%;
    position: relative;
    z-index: 2;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 24px;
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);

    .header-left {
      .page-title {
        margin: 0 0 8px 0;
        font-size: 28px;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: flex;
        align-items: center;
        gap: 12px;
        
        .el-icon {
          font-size: 32px;
          color: #667eea;
        }
      }

      .page-description {
        margin: 0;
        color: #64748b;
        font-size: 16px;
      }
    }

    .header-actions {
      display: flex;
      gap: 12px;
      
      .el-button {
        border-radius: 12px;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
        
        &.el-button--primary {
          background: linear-gradient(135deg, #667eea, #764ba2);
          border: none;
          color: white;
          
          &:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
          }
        }
      }
    }
  }

  .main-content {
    flex: 1;
    display: flex;
    gap: 20px;
    min-height: 0;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 20px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    position: relative;
    z-index: 1;
  }

  .user-list-panel {
    width: 400px;
    height: 600px;
    flex-shrink: 0;

    .list-card {
      height: 100%;
      display: flex;
      flex-direction: column;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);

      :deep(.el-card__header) {
        background: linear-gradient(135deg, #f8fafc, #e2e8f0);
        border-bottom: 1px solid rgba(226, 232, 240, 0.5);
        border-radius: 16px 16px 0 0;
      }

      :deep(.el-card__body) {
        flex: 1;
        display: flex;
        flex-direction: column;
        padding: 0;
      }

      .list-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0px;
        border-bottom: 1px solid #ebeef5;

        .list-title {
          font-weight: 600;
          color: #303133;
          display: flex;
          align-items: center;
          gap: 6px;
        }
      }

      .user-list-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-height: 0;
        max-height: 500px;

        .loading-container,
        .empty-container {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .user-items {
          flex: 1;
          max-height: 500px;
          overflow-y: scroll;
          padding: 0;
          
          // 自定义滚动条样式
          &::-webkit-scrollbar {
            width: 8px;
          }
          
          &::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.1);
            border-radius: 4px;
          }
          
          &::-webkit-scrollbar-thumb {
            background: rgba(102, 126, 234, 0.6);
            border-radius: 4px;
            
            &:hover {
              background: rgba(102, 126, 234, 0.8);
            }
          }

          .user-item {
            padding: 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            cursor: pointer;
            transition: all 0.3s;
            border-radius: 12px;
            margin: 0 16px 8px 16px;
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);

            &:hover {
              background: rgba(255, 255, 255, 0.9);
              box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
              transform: translateY(-2px);
              border-color: #667eea;
            }

            &.active {
              background: rgba(102, 126, 234, 0.1);
              border-left: 3px solid #667eea;
              box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
            }

            .user-item-header {
              display: flex;
              justify-content: space-between;
              align-items: flex-start;
              margin-bottom: 12px;

              .user-info {
                display: flex;
                align-items: center;
                gap: 12px;

                .user-details {
                  .user-name {
                    margin: 0;
                    font-size: 16px;
                    font-weight: 600;
                    color: #303133;
                    line-height: 1.4;
                  }

                  .user-email {
                    margin: 4px 0 0 0;
                    font-size: 12px;
                    color: #909399;
                  }
                }
              }

              .user-actions {
                display: flex;
                align-items: center;
                gap: 8px;
              }
            }
            
            .user-item-content {
              .user-meta {
                display: flex;
                flex-wrap: wrap;
                gap: 12px;
                margin-bottom: 8px;

                .meta-item {
                  display: flex;
                  align-items: center;
                  gap: 4px;
                  font-size: 12px;
                  color: #606266;
                }
              }

              .user-time {
                font-size: 12px;
                color: #909399;
              }
            }
          }
        }

        .pagination-container {
          margin-top: 16px;
          display: flex;
          justify-content: center;
        }
      }
    }
  }

  .user-editor-panel {
    flex: 1;
    min-width: 0;

    .welcome-container {
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;

      .welcome-card {
        width: 100%;
        max-width: 500px;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);

        .welcome-content {
          text-align: center;
          padding: 40px 20px;

          .welcome-icon {
            margin-bottom: 24px;
            color: #409eff;
          }

          h2 {
            margin: 0 0 16px 0;
            color: #303133;
            font-size: 24px;
          }

          p {
            margin: 0 0 32px 0;
            color: #606266;
            font-size: 16px;
          }

          .welcome-actions {
            display: flex;
            justify-content: center;
            gap: 16px;
          }
        }
      }
    }

    .user-editor-content {
      height: 100%;
      display: flex;
      flex-direction: column;

      .editor-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 20px 24px;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);

        .editor-title {
          display: flex;
          align-items: center;
          gap: 12px;

          h3 {
            margin: 0;
            color: #303133;
            font-size: 18px;
            font-weight: 600;
          }
        }

        .editor-actions {
          display: flex;
          gap: 12px;

          .el-button {
            border-radius: 12px;
            font-weight: 600;
            padding: 12px 24px;
            transition: all 0.3s ease;

            &.el-button--primary {
              background: linear-gradient(135deg, #667eea, #764ba2);
              border: none;
              color: white;

              &:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
              }
            }

            &:not(.el-button--primary) {
              background: rgba(255, 255, 255, 0.8);
              border: 1px solid rgba(226, 232, 240, 0.8);
              color: #64748b;

              &:hover {
                background: rgba(248, 250, 252, 0.9);
                border-color: rgba(102, 126, 234, 0.3);
                color: #667eea;
                transform: translateY(-2px);
              }
            }
          }
        }
      }

      .editor-main {
        flex: 1;
        min-height: 0;

        .user-form-card {
          height: 100%;
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 16px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);

          :deep(.el-card__header) {
            background: linear-gradient(135deg, #f8fafc, #e2e8f0);
            border-bottom: 1px solid rgba(226, 232, 240, 0.5);
            border-radius: 16px 16px 0 0;
          }

          :deep(.el-card__body) {
            padding: 20px;
            height: calc(100% - 60px);
            overflow-y: auto;
          }

          .card-header {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            color: #303133;
          }

          .user-form {
            padding-right: 8px;
          }
        }
      }
    }
  }
}

// 背景动画
@keyframes float {
  0% {
    transform: translate(0, 0) rotate(0deg);
  }
  33% {
    transform: translate(30px, -30px) rotate(120deg);
  }
  66% {
    transform: translate(-20px, 20px) rotate(240deg);
  }
  100% {
    transform: translate(0, 0) rotate(360deg);
  }
}

// 响应式设计
@media (max-width: 1400px) {
  .user-management {
    .main-content {
      .user-list-panel {
        width: 320px;
      }
    }
  }
}

@media (max-width: 1200px) {
  .user-management {
    .main-content {
      flex-direction: column;

      .user-list-panel {
        width: 100%;
        height: 300px;
      }
    }
  }
}
</style>
