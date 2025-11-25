<template>
  <div class="admin-dashboard">
    <div class="page-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Setting /></el-icon>
            系统管理
          </h1>
          <p class="page-description">系统配置、用户管理、权限控制、邮箱服务管理</p>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-section">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover" @click="navigateTo('users')">
              <div class="stat-content">
                <div class="stat-icon users">
                  <el-icon size="32"><User /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{ stats.users }}</div>
                  <div class="stat-label">系统用户</div>
                </div>
              </div>
              <div class="stat-footer">
                <span>查看详情</span>
                <el-icon><ArrowRight /></el-icon>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover" @click="navigateTo('roles')">
              <div class="stat-content">
                <div class="stat-icon roles">
                  <el-icon size="32"><Avatar /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{ stats.roles }}</div>
                  <div class="stat-label">用户角色</div>
                </div>
              </div>
              <div class="stat-footer">
                <span>查看详情</span>
                <el-icon><ArrowRight /></el-icon>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover" @click="navigateTo('email-configs')">
              <div class="stat-content">
                <div class="stat-icon emails">
                  <el-icon size="32"><Message /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{ stats.emails }}</div>
                  <div class="stat-label">邮箱配置</div>
                </div>
              </div>
              <div class="stat-footer">
                <span>查看详情</span>
                <el-icon><ArrowRight /></el-icon>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover">
              <div class="stat-content">
                <div class="stat-icon system">
                  <el-icon size="32"><Monitor /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{ stats.onlineUsers }}</div>
                  <div class="stat-label">在线用户</div>
                </div>
              </div>
              <div class="stat-footer">
                <span>系统状态</span>
                <el-icon><ArrowRight /></el-icon>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 快捷操作 -->
      <div class="quick-actions-section">
        <el-card class="actions-card">
          <template #header>
            <div class="card-header">
              <el-icon><Operation /></el-icon>
              <span>快捷操作</span>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="action-item" @click="navigateTo('users')">
                <div class="action-icon users">
                  <el-icon size="24"><User /></el-icon>
                </div>
                <div class="action-content">
                  <h4>用户管理</h4>
                  <p>创建用户、分配角色、管理用户状态</p>
                </div>
                <el-icon class="action-arrow"><ArrowRight /></el-icon>
              </div>
            </el-col>
            
            <el-col :span="8">
              <div class="action-item" @click="navigateTo('roles')">
                <div class="action-icon roles">
                  <el-icon size="24"><Avatar /></el-icon>
                </div>
                <div class="action-content">
                  <h4>角色权限</h4>
                  <p>配置角色权限、管理访问控制</p>
                </div>
                <el-icon class="action-arrow"><ArrowRight /></el-icon>
              </div>
            </el-col>
            
            <el-col :span="8">
              <div class="action-item" @click="navigateTo('email-configs')">
                <div class="action-icon emails">
                  <el-icon size="24"><Message /></el-icon>
                </div>
                <div class="action-content">
                  <h4>邮箱配置</h4>
                  <p>配置招聘邮箱、自动抓取简历</p>
                </div>
                <el-icon class="action-arrow"><ArrowRight /></el-icon>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </div>

      <!-- 最近活动 -->
      <div class="recent-activity-section">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card class="activity-card">
              <template #header>
                <div class="card-header">
                  <el-icon><Clock /></el-icon>
                  <span>最近用户活动</span>
                  <el-button text size="small" @click="navigateTo('users')">
                    查看更多
                  </el-button>
                </div>
              </template>
              
              <div class="activity-list">
                <div v-if="recentUsers.length === 0" class="empty-activity">
                  <el-empty description="暂无用户活动" :image-size="80" />
                </div>
                
                <div v-else>
                  <div 
                    v-for="user in recentUsers" 
                    :key="user.id" 
                    class="activity-item"
                  >
                    <el-avatar :size="32" :src="user.avatar_url">
                      <el-icon><User /></el-icon>
                    </el-avatar>
                    <div class="activity-content">
                      <div class="activity-title">
                        <span class="user-name">{{ user.full_name || user.username }}</span>
                        <span class="activity-action">{{ user.last_action }}</span>
                      </div>
                      <div class="activity-time">{{ formatTime(user.last_active_at) }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="12">
            <el-card class="activity-card">
              <template #header>
                <div class="card-header">
                  <el-icon><Message /></el-icon>
                  <span>最近邮箱活动</span>
                  <el-button text size="small" @click="navigateTo('email-configs')">
                    查看更多
                  </el-button>
                </div>
              </template>
              
              <div class="activity-list">
                <div v-if="recentEmails.length === 0" class="empty-activity">
                  <el-empty description="暂无邮箱活动" :image-size="80" />
                </div>
                
                <div v-else>
                  <div 
                    v-for="email in recentEmails" 
                    :key="email.id" 
                    class="activity-item"
                  >
                    <div class="activity-icon">
                      <el-icon size="20"><Message /></el-icon>
                    </div>
                    <div class="activity-content">
                      <div class="activity-title">
                        <span class="email-name">{{ email.name }}</span>
                        <span class="activity-action">
                          抓取到 {{ email.emails_found }} 封邮件，{{ email.resumes_extracted }} 份简历
                        </span>
                      </div>
                      <div class="activity-time">{{ formatTime(email.created_at) }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Setting,
  User,
  Avatar,
  Message,
  Monitor,
  Operation,
  ArrowRight,
  Clock
} from '@element-plus/icons-vue'

const router = useRouter()

// 统计数据
const stats = reactive({
  users: 0,
  roles: 0,
  emails: 0,
  onlineUsers: 0
})

// 最近活动数据
const recentUsers = ref([])
const recentEmails = ref([])

// 方法
const navigateTo = (path) => {
  router.push(`/admin/${path}`)
}

const fetchStats = async () => {
  try {
    // TODO: 调用获取统计数据的API
    console.log('获取统计数据')
    
    // 模拟数据
    stats.users = 128
    stats.roles = 8
    stats.emails = 5
    stats.onlineUsers = 23
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const fetchRecentActivity = async () => {
  try {
    // TODO: 调用获取最近活动的API
    console.log('获取最近活动')
    
    // 模拟用户活动数据
    recentUsers.value = [
      {
        id: '1',
        username: 'admin',
        full_name: '系统管理员',
        avatar_url: '',
        last_action: '登录系统',
        last_active_at: new Date(Date.now() - 300000).toISOString() // 5分钟前
      },
      {
        id: '2',
        username: 'hr1',
        full_name: 'HR专员',
        avatar_url: '',
        last_action: '创建了新的JD',
        last_active_at: new Date(Date.now() - 1800000).toISOString() // 30分钟前
      },
      {
        id: '3',
        username: 'hr2',
        full_name: '招聘经理',
        avatar_url: '',
        last_action: '筛选简历',
        last_active_at: new Date(Date.now() - 3600000).toISOString() // 1小时前
      }
    ]
    
    // 模拟邮箱活动数据
    recentEmails.value = [
      {
        id: '1',
        name: '主招聘邮箱',
        emails_found: 12,
        resumes_extracted: 8,
        created_at: new Date(Date.now() - 600000).toISOString() // 10分钟前
      },
      {
        id: '2',
        name: '技术招聘邮箱',
        emails_found: 5,
        resumes_extracted: 3,
        created_at: new Date(Date.now() - 3600000).toISOString() // 1小时前
      }
    ]
  } catch (error) {
    console.error('获取最近活动失败:', error)
  }
}

const formatTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (minutes < 1440) return `${Math.floor(minutes / 60)}小时前`
  return date.toLocaleDateString('zh-CN')
}

// 生命周期
onMounted(async () => {
  await fetchStats()
  await fetchRecentActivity()
})
</script>

<style lang="scss" scoped>
.admin-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  
  .page-container {
    max-width: 1400px;
    margin: 0 auto;
  }

  .page-header {
    margin-bottom: 30px;
    text-align: center;
    
    .page-title {
      font-size: 32px;
      font-weight: 700;
      color: white;
      margin: 0 0 12px 0;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      
      .el-icon {
        font-size: 36px;
        color: rgba(255, 255, 255, 0.9);
      }
    }
    
    .page-description {
      font-size: 18px;
      color: rgba(255, 255, 255, 0.8);
      margin: 0;
    }
  }

  .stats-section {
    margin-bottom: 30px;
    
    .stat-card {
      border-radius: 16px;
      border: none;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
      }
      
      .stat-content {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 24px 20px;
        
        .stat-icon {
          width: 60px;
          height: 60px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          
          &.users {
            background: linear-gradient(135deg, #667eea, #764ba2);
          }
          
          &.roles {
            background: linear-gradient(135deg, #f093fb, #f5576c);
          }
          
          &.emails {
            background: linear-gradient(135deg, #4facfe, #00f2fe);
          }
          
          &.system {
            background: linear-gradient(135deg, #43e97b, #38f9d7);
          }
        }
        
        .stat-info {
          text-align: right;
          
          .stat-number {
            font-size: 28px;
            font-weight: 700;
            color: #303133;
            margin-bottom: 4px;
          }
          
          .stat-label {
            font-size: 14px;
            color: #909399;
          }
        }
      }
      
      .stat-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 20px;
        border-top: 1px solid #f0f2f5;
        font-size: 13px;
        color: #909399;
        
        .el-icon {
          font-size: 14px;
        }
      }
    }
  }

  .quick-actions-section {
    margin-bottom: 30px;
    
    .actions-card {
      border-radius: 16px;
      border: none;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      
      :deep(.el-card__header) {
        background: linear-gradient(135deg, #f8fafc, #e2e8f0);
        border-bottom: 1px solid rgba(226, 232, 240, 0.5);
        border-radius: 16px 16px 0 0;
        padding: 20px 24px;
      }
      
      .card-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        color: #303133;
      }
      
      .action-item {
        display: flex;
        align-items: center;
        padding: 24px;
        border-radius: 12px;
        background: #f8fafc;
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover {
          background: #f1f5f9;
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }
        
        .action-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          margin-right: 16px;
          
          &.users {
            background: linear-gradient(135deg, #667eea, #764ba2);
          }
          
          &.roles {
            background: linear-gradient(135deg, #f093fb, #f5576c);
          }
          
          &.emails {
            background: linear-gradient(135deg, #4facfe, #00f2fe);
          }
        }
        
        .action-content {
          flex: 1;
          
          h4 {
            margin: 0 0 8px 0;
            font-size: 16px;
            font-weight: 600;
            color: #303133;
          }
          
          p {
            margin: 0;
            font-size: 14px;
            color: #606266;
            line-height: 1.5;
          }
        }
        
        .action-arrow {
          color: #909399;
          font-size: 16px;
        }
      }
    }
  }

  .recent-activity-section {
    .activity-card {
      border-radius: 16px;
      border: none;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      height: 400px;
      
      :deep(.el-card__header) {
        background: linear-gradient(135deg, #f8fafc, #e2e8f0);
        border-bottom: 1px solid rgba(226, 232, 240, 0.5);
        border-radius: 16px 16px 0 0;
        padding: 20px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      
      .card-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        color: #303133;
      }
      
      .activity-list {
        height: calc(100% - 60px);
        overflow-y: auto;
        padding: 0;
        
        .empty-activity {
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .activity-item {
          display: flex;
          align-items: center;
          padding: 16px 24px;
          border-bottom: 1px solid #f0f2f5;
          transition: background 0.3s ease;
          
          &:hover {
            background: #f8fafc;
          }
          
          &:last-child {
            border-bottom: none;
          }
          
          .el-avatar {
            margin-right: 16px;
            flex-shrink: 0;
          }
          
          .activity-icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: linear-gradient(135deg, #4facfe, #00f2fe);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            margin-right: 16px;
            flex-shrink: 0;
          }
          
          .activity-content {
            flex: 1;
            
            .activity-title {
              display: flex;
              align-items: center;
              gap: 8px;
              margin-bottom: 4px;
              
              .user-name, .email-name {
                font-weight: 500;
                color: #303133;
              }
              
              .activity-action {
                color: #606266;
                font-size: 14px;
              }
            }
            
            .activity-time {
              font-size: 12px;
              color: #909399;
            }
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .admin-dashboard {
    .stats-section {
      .el-col {
        margin-bottom: 20px;
      }
    }
    
    .quick-actions-section {
      .action-item {
        margin-bottom: 16px;
      }
    }
  }
}

@media (max-width: 768px) {
  .admin-dashboard {
    padding: 16px;
    
    .page-header {
      .page-title {
        font-size: 24px;
        
        .el-icon {
          font-size: 28px;
        }
      }
      
      .page-description {
        font-size: 16px;
      }
    }
    
    .stats-section {
      .el-col {
        margin-bottom: 16px;
      }
    }
  }
}
</style>