<template>
  <div class="role-management" v-loading="loading">
    <div class="page-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Avatar /></el-icon>
            角色管理
          </h1>
          <p class="page-description">管理系统角色，配置角色权限，控制用户访问范围</p>
        </div>
        <div class="header-actions">
          <el-button @click="createNewRole" type="primary" size="large">
            <el-icon><Plus /></el-icon>
            新增角色
          </el-button>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <div class="main-content">
        <!-- 左侧角色列表 -->
        <div class="role-list-panel">
          <el-card class="list-card">
            <template #header>
              <div class="list-header">
                <span class="list-title">
                  <el-icon><List /></el-icon>
                  角色列表 ({{ pagination.total }})
                </span>
                <div class="list-actions">
                  <el-input
                    v-model="searchKeyword"
                    placeholder="搜索角色名称..."
                    clearable
                    size="small"
                    style="width: 200px"
                    @input="handleSearch"
                  >
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                </div>
              </div>
            </template>

            <!-- 角色列表内容 -->
            <div class="role-list-content">
              <div v-if="roleListLoading" class="loading-container">
                <el-skeleton :rows="5" animated />
              </div>
              
              <div v-else-if="roleList.length === 0" class="empty-container">
                <el-empty description="暂无角色数据" :image-size="120">
                  <el-button type="primary" @click="createNewRole">
                    <el-icon><Plus /></el-icon>
                    创建第一个角色
                  </el-button>
                </el-empty>
              </div>

              <div v-else class="role-items">
                <div
                  v-for="role in roleList"
                  :key="role.id"
                  :class="['role-item', { active: selectedRole?.id === role.id, builtin: role.is_builtin }]"
                  @click="selectRole(role)"
                >
                  <div class="role-item-header">
                    <div class="role-info">
                      <h4 class="role-name">{{ role.name }}</h4>
                      <el-tag v-if="role.is_builtin" type="info" size="small">内置</el-tag>
                    </div>
                    <div class="role-actions" v-if="!role.is_builtin">
                      <el-dropdown trigger="click" @command="handleRoleAction">
                        <el-button text size="small">
                          <el-icon><MoreFilled /></el-icon>
                        </el-button>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item :command="{ action: 'edit', role }">
                              <el-icon><Edit /></el-icon>
                              编辑
                            </el-dropdown-item>
                            <el-dropdown-item :command="{ action: 'delete', role }" divided>
                              <el-icon><Delete /></el-icon>
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                  </div>
                  
                  <div class="role-item-content">
                    <p class="role-description">{{ role.description || '暂无描述' }}</p>
                    <div class="role-stats">
                      <span class="stat-item">
                        <el-icon><User /></el-icon>
                        {{ getRoleUserCount(role.id) }} 个用户
                      </span>
                      <span class="stat-item">
                        <el-icon><Key /></el-icon>
                        {{ role.permissions?.length || 0 }} 项权限
                      </span>
                    </div>
                    <div class="role-time">
                      创建时间: {{ formatDate(role.created_at) }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- 分页 -->
              <div v-if="roleList.length > 0" class="pagination-container">
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
        <div class="role-editor-panel">
          <!-- 欢迎页面 -->
          <div v-if="!selectedRole && !isCreatingNew" class="welcome-container">
            <el-card class="welcome-card">
              <div class="welcome-content">
                <div class="welcome-icon">
                  <el-icon size="80"><Avatar /></el-icon>
                </div>
                <h2>欢迎使用角色管理</h2>
                <p>选择左侧的角色进行编辑，或创建新角色</p>
                <div class="welcome-actions">
                  <el-button type="primary" @click="createNewRole" size="large">
                    <el-icon><Plus /></el-icon>
                    创建新角色
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>

          <!-- 角色编辑区域 -->
          <div v-else class="role-editor-content">
            <!-- 编辑器头部 -->
            <div class="editor-header">
              <div class="editor-title">
                <h3>{{ isCreatingNew ? '创建新角色' : `编辑角色: ${selectedRole?.name}` }}</h3>
                <el-tag v-if="selectedRole?.is_builtin" type="info" size="small">内置角色</el-tag>
              </div>
              <div class="editor-actions">
                <el-button @click="resetRoleForm" :disabled="saving">
                  <el-icon><Refresh /></el-icon>
                  重置
                </el-button>
                <el-button 
                  type="primary" 
                  @click="saveRole" 
                  :loading="saving"
                  :disabled="selectedRole?.is_builtin && !isCreatingNew"
                >
                  <el-icon><Check /></el-icon>
                  保存
                </el-button>
              </div>
            </div>

            <!-- 编辑器主要内容 -->
            <div class="editor-main">
              <el-form
                ref="roleFormRef"
                :model="roleForm"
                :rules="roleRules"
                label-width="100px"
                label-position="top"
                class="role-form"
              >
                <el-card class="form-card">
                  <template #header>
                    <div class="card-header">
                      <el-icon><InfoFilled /></el-icon>
                      <span>基本信息</span>
                    </div>
                  </template>

                  <el-form-item label="角色名称" prop="name">
                    <el-input 
                      v-model="roleForm.name" 
                      placeholder="请输入角色名称"
                      :disabled="selectedRole?.is_builtin && !isCreatingNew"
                    />
                  </el-form-item>

                  <el-form-item label="角色描述" prop="description">
                    <el-input 
                      v-model="roleForm.description" 
                      type="textarea"
                      :rows="3"
                      placeholder="请输入角色描述"
                      :disabled="selectedRole?.is_builtin && !isCreatingNew"
                    />
                  </el-form-item>

                  <el-form-item label="角色状态" prop="status">
                    <el-radio-group v-model="roleForm.status" :disabled="selectedRole?.is_builtin && !isCreatingNew">
                      <el-radio label="active">启用</el-radio>
                      <el-radio label="inactive">禁用</el-radio>
                    </el-radio-group>
                  </el-form-item>
                </el-card>

                <el-card class="form-card permission-card" v-if="false">
                  <template #header>
                    <div class="card-header">
                      <el-icon><Key /></el-icon>
                      <span>权限配置</span>
                      <div class="permission-actions">
                        <el-button @click="selectAllPermissions" size="small">
                          全选
                        </el-button>
                        <el-button @click="clearAllPermissions" size="small">
                          清空
                        </el-button>
                      </div>
                    </div>
                  </template>

                  <div class="permission-tree-container">
                    <el-tree
                      ref="permissionTreeRef"
                      :data="permissionTree"
                      :props="treeProps"
                      show-checkbox
                      node-key="id"
                      :default-checked-keys="selectedPermissions"
                      @check-change="handlePermissionChange"
                    >
                      <template #default="{ node, data }">
                        <div class="permission-node">
                          <div class="permission-info">
                            <span class="permission-name">{{ data.name }}</span>
                            <span class="permission-code">{{ data.code }}</span>
                          </div>
                          <span class="permission-description">{{ data.description }}</span>
                        </div>
                      </template>
                    </el-tree>
                  </div>
                </el-card>
              </el-form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Avatar,
  Plus,
  List,
  Search,
  MoreFilled,
  Edit,
  Delete,
  User,
  Key,
  Refresh,
  Check,
  InfoFilled
} from '@element-plus/icons-vue'
import { roleApi } from '@/api/admin'

// 响应式数据
const loading = ref(false)
const saving = ref(false)

// 角色列表相关
const roleList = ref([])
const roleListLoading = ref(false)
const selectedRole = ref(null)
const isCreatingNew = ref(false)
const searchKeyword = ref('')

// 权限相关
const permissionTree = ref([])
const selectedPermissions = ref([])
const permissionTreeRef = ref()

// 分页数据
const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

// 角色表单
const roleFormRef = ref()
const roleForm = reactive({
  name: '',
  description: '',
  status: 'active',
  permissions: []
})

// 表单验证规则
const roleRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 50, message: '角色名称长度在2-50个字符之间', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '角色描述不能超过500个字符', trigger: 'blur' }
  ]
}

// 树形控件配置
const treeProps = {
  children: 'children',
  label: 'name'
}

// 模拟用户数据（实际应该从API获取）
const userData = ref([
  { id: '1', username: 'admin', role_id: '1' },
  { id: '2', username: 'hr1', role_id: '2' },
  { id: '3', username: 'hr2', role_id: '2' }
])

// 计算属性
const getRoleUserCount = (roleId) => {
  return userData.value.filter(user => user.role_id === roleId).length
}

// 方法
const createNewRole = () => {
  isCreatingNew.value = true
  selectedRole.value = null
  resetRoleForm()
}

const selectRole = (role) => {
  selectedRole.value = role
  isCreatingNew.value = false
  
  // 填充表单数据
  roleForm.name = role.name
  roleForm.description = role.description || ''
  roleForm.status = role.status || 'active'
  roleForm.permissions = role.permissions || []
  
  // 设置选中的权限
  selectedPermissions.value = role.permissions?.map(p => p.id) || []
}

const resetRoleForm = () => {
  roleForm.name = ''
  roleForm.description = ''
  roleForm.status = 'active'
  roleForm.permissions = []
  selectedPermissions.value = []
  
  if (roleFormRef.value) {
    roleFormRef.value.clearValidate()
  }
  if (permissionTreeRef.value) {
    permissionTreeRef.value.setCheckedKeys([])
  }
}

const saveRole = async () => {
  try {
    await roleFormRef.value.validate()
    saving.value = true
    
    // 获取选中的权限
    const checkedKeys = permissionTreeRef.value.getCheckedKeys()
    const halfCheckedKeys = permissionTreeRef.value.getHalfCheckedKeys()
    const allCheckedKeys = [...checkedKeys, ...halfCheckedKeys]
    
    const roleData = {
      name: roleForm.name,
      description: roleForm.description,
      status: roleForm.status,
      permissions: allCheckedKeys
    }
    
    if (isCreatingNew.value) {
      // 调用创建角色API
      await roleApi.createRole(roleData)
      ElMessage.success('角色创建成功')
    } else {
      // 调用更新角色API
      await roleApi.updateRole(selectedRole.value.id, roleData)
      ElMessage.success('角色更新成功')
    }
    
    await fetchRoleList()
  } catch (error) {
    console.error('保存角色失败:', error)
    ElMessage.error('保存角色失败，请重试')
  } finally {
    saving.value = false
  }
}

const handleRoleAction = async ({ action, role }) => {
  switch (action) {
    case 'edit':
      selectRole(role)
      break
    case 'delete':
      await deleteRole(role)
      break
  }
}

const deleteRole = async (role) => {
  try {
    const userCount = getRoleUserCount(role.id)
    if (userCount > 0) {
      ElMessage.warning(`该角色下还有 ${userCount} 个用户，不能删除`)
      return
    }
    
    await ElMessageBox.confirm(
      `确定要删除角色"${role.name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 调用删除角色API
    await roleApi.deleteRole(role.id)
    ElMessage.success('角色删除成功')
    
    if (selectedRole.value?.id === role.id) {
      selectedRole.value = null
      isCreatingNew.value = false
    }
    
    await fetchRoleList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除角色失败:', error)
      ElMessage.error('删除角色失败')
    }
  }
}

const handlePermissionChange = () => {
  // 权限选择变化时的处理
  const checkedKeys = permissionTreeRef.value.getCheckedKeys()
  console.log('当前选中的权限:', checkedKeys)
}

const selectAllPermissions = () => {
  const allNodeIds = getAllNodeIds(permissionTree.value)
  permissionTreeRef.value.setCheckedKeys(allNodeIds)
}

const clearAllPermissions = () => {
  permissionTreeRef.value.setCheckedKeys([])
}

const getAllNodeIds = (nodes) => {
  let ids = []
  nodes.forEach(node => {
    ids.push(node.id)
    if (node.children && node.children.length > 0) {
      ids = ids.concat(getAllNodeIds(node.children))
    }
  })
  return ids
}

const fetchRoleList = async () => {
  try {
    roleListLoading.value = true
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    
    // 调用获取角色列表API
    const response = await roleApi.getRoleList(params)
    if (Array.isArray(response)) {
      roleList.value = response
      pagination.total = response.length || 0
    } else {
      roleList.value = response.items || []
      pagination.total = response.total || (roleList.value.length || 0)
    }
  } catch (error) {
    console.error('获取角色列表失败:', error)
    ElMessage.error('获取角色列表失败')
  } finally {
    roleListLoading.value = false
  }
}

const fetchPermissionList = async () => {
  try {
    permissionTree.value = []
  } catch (error) {
    console.error('获取权限列表失败:', error)
    ElMessage.error('获取权限列表失败')
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchRoleList()
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchRoleList()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchRoleList()
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

// 生命周期
onMounted(async () => {
  await fetchRoleList()
})
</script>

<style lang="scss" scoped>
.role-management {
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

  .role-list-panel {
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
        padding: 16px;
        border-bottom: 1px solid #ebeef5;

        .list-title {
          font-weight: 600;
          color: #303133;
          display: flex;
          align-items: center;
          gap: 6px;
        }
      }

      .role-list-content {
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

        .role-items {
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

          .role-item {
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

            &.builtin {
              background: rgba(245, 247, 250, 0.8);
              
              &:hover {
                background: rgba(245, 247, 250, 0.9);
              }
            }

            .role-item-header {
              display: flex;
              justify-content: space-between;
              align-items: flex-start;
              margin-bottom: 12px;

              .role-info {
                display: flex;
                align-items: center;
                gap: 8px;

                .role-name {
                  margin: 0;
                  font-size: 16px;
                  font-weight: 600;
                  color: #303133;
                  line-height: 1.4;
                }
              }
            }
            
            .role-item-content {
              .role-description {
                margin: 0 0 12px 0;
                font-size: 14px;
                color: #606266;
                line-height: 1.5;
              }

              .role-stats {
                display: flex;
                flex-wrap: wrap;
                gap: 12px;
                margin-bottom: 8px;

                .stat-item {
                  display: flex;
                  align-items: center;
                  gap: 4px;
                  font-size: 12px;
                  color: #606266;
                }
              }

              .role-time {
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

  .role-editor-panel {
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

    .role-editor-content {
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

        .role-form {
          height: 100%;
          display: flex;
          flex-direction: column;
          gap: 20px;

          .form-card {
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
            }

            .card-header {
              display: flex;
              align-items: center;
              gap: 8px;
              font-weight: 600;
              color: #303133;
            }

            &.permission-card {
              flex: 1;
              display: flex;
              flex-direction: column;
              min-height: 0;

              :deep(.el-card__body) {
                flex: 1;
                display: flex;
                flex-direction: column;
                min-height: 0;
                padding: 0;
              }

              .card-header {
                justify-content: space-between;

                .permission-actions {
                  display: flex;
                  gap: 8px;
                }
              }

              .permission-tree-container {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                
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

                .permission-node {
                  display: flex;
                  align-items: center;
                  justify-content: space-between;
                  width: 100%;
                  padding: 4px 0;

                  .permission-info {
                    display: flex;
                    align-items: center;
                    gap: 8px;

                    .permission-name {
                      font-weight: 500;
                      color: #303133;
                    }

                    .permission-code {
                      font-size: 12px;
                      color: #909399;
                      background: #f5f7fa;
                      padding: 2px 6px;
                      border-radius: 4px;
                    }
                  }

                  .permission-description {
                    font-size: 12px;
                    color: #606266;
                    margin-left: 8px;
                  }
                }
              }
            }
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
  .role-management {
    .main-content {
      .role-list-panel {
        width: 320px;
      }
    }
  }
}

@media (max-width: 1200px) {
  .role-management {
    .main-content {
      flex-direction: column;

      .role-list-panel {
        width: 100%;
        height: 300px;
      }
    }
  }
}
</style>
