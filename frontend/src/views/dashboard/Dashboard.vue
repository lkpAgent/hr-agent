<template>
  <div class="dashboard">
    <div class="page-container">
      <!-- 欢迎区域 -->
      <div class="welcome-section">
        <div class="welcome-content">
          <h1 class="welcome-title">
            欢迎回来，{{ user?.full_name || user?.username }}！
          </h1>
          <p class="welcome-subtitle">
            今天是 {{ currentDate }}，让我们开始高效的工作吧
          </p>
        </div>
        <div class="welcome-actions">
          <el-button type="primary" size="large" @click="$router.push('/recruitment/jd-generator')">
            <el-icon><Plus /></el-icon>
            创建JD
          </el-button>
          <el-button size="large" @click="$router.push('/assistant/chat')">
            <el-icon><ChatDotRound /></el-icon>
            智能助理
          </el-button>
        </div>
      </div>

      <!-- 数据统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon recruitment">
            <el-icon><UserFilled /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.recruitment.total }}</div>
            <div class="stat-label">招聘职位</div>
            <div class="stat-change positive">
              <el-icon><TrendCharts /></el-icon>
              +{{ stats.recruitment.change }}%
            </div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon training">
            <el-icon><Reading /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.training.total }}</div>
            <div class="stat-label">培训课程</div>
            <div class="stat-change positive">
              <el-icon><TrendCharts /></el-icon>
              +{{ stats.training.change }}%
            </div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon interview">
            <el-icon><VideoCamera /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.interview.total }}</div>
            <div class="stat-label">面试安排</div>
            <div class="stat-change negative">
              <el-icon><TrendCharts /></el-icon>
              {{ stats.interview.change }}%
            </div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon assistant">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.assistant.total }}</div>
            <div class="stat-label">AI对话</div>
            <div class="stat-change positive">
              <el-icon><TrendCharts /></el-icon>
              +{{ stats.assistant.change }}%
            </div>
          </div>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <div class="main-grid">
        <!-- 快捷操作 -->
        <div class="quick-actions-card">
          <div class="card-header">
            <h3>快捷操作</h3>
          </div>
          <div class="quick-actions-grid">
            <div class="quick-action" @click="$router.push('/recruitment/jd-generator')">
              <div class="action-icon recruitment">
                <el-icon><Document /></el-icon>
              </div>
              <div class="action-content">
                <h4>生成JD</h4>
                <p>AI智能生成职位描述</p>
              </div>
            </div>

            <div class="quick-action" @click="$router.push('/recruitment/resume-screening')">
              <div class="action-icon recruitment">
                <el-icon><Files /></el-icon>
              </div>
              <div class="action-content">
                <h4>简历筛选</h4>
                <p>智能筛选候选人简历</p>
              </div>
            </div>

            <div class="quick-action" @click="$router.push('/training/exam-generator')">
              <div class="action-icon training">
                <el-icon><EditPen /></el-icon>
              </div>
              <div class="action-content">
                <h4>生成试卷</h4>
                <p>基于知识库生成考试</p>
              </div>
            </div>

            <div class="quick-action" @click="$router.push('/assistant/chat')">
              <div class="action-icon assistant">
                <el-icon><ChatDotRound /></el-icon>
              </div>
              <div class="action-content">
                <h4>智能问答</h4>
                <p>AI助理解答疑问</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 最近活动 -->
        <div class="recent-activities-card">
          <div class="card-header">
            <h3>最近活动</h3>
            <el-link type="primary">查看全部</el-link>
          </div>
          <div class="activities-list">
            <div 
              v-for="activity in recentActivities" 
              :key="activity.id"
              class="activity-item"
            >
              <div class="activity-icon" :class="activity.type">
                <el-icon><component :is="activity.icon" /></el-icon>
              </div>
              <div class="activity-content">
                <div class="activity-title">{{ activity.title }}</div>
                <div class="activity-time">{{ activity.time }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 图表区域 -->
      <div class="charts-grid">
        <div class="chart-card">
          <div class="card-header">
            <h3>招聘趋势</h3>
            <el-select v-model="chartPeriod" size="small">
              <el-option label="最近7天" value="7d" />
              <el-option label="最近30天" value="30d" />
              <el-option label="最近90天" value="90d" />
            </el-select>
          </div>
          <div class="chart-container">
            <v-chart :option="recruitmentChartOption" style="height: 300px;" />
          </div>
        </div>

        <div class="chart-card">
          <div class="card-header">
            <h3>培训完成率</h3>
          </div>
          <div class="chart-container">
            <v-chart :option="trainingChartOption" style="height: 300px;" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import dayjs from 'dayjs'

// 注册ECharts组件
use([
  CanvasRenderer,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const authStore = useAuthStore()

// 响应式数据
const chartPeriod = ref('30d')

// 计算属性
const user = computed(() => authStore.user)
const currentDate = computed(() => dayjs().format('YYYY年MM月DD日'))

// 模拟数据
const stats = ref({
  recruitment: { total: 156, change: 12 },
  training: { total: 89, change: 8 },
  interview: { total: 23, change: -5 },
  assistant: { total: 342, change: 25 }
})

const recentActivities = ref([
  {
    id: 1,
    type: 'recruitment',
    icon: 'Document',
    title: '生成了前端开发工程师JD',
    time: '2分钟前'
  },
  {
    id: 2,
    type: 'training',
    icon: 'Reading',
    title: '创建了JavaScript基础培训课程',
    time: '15分钟前'
  },
  {
    id: 3,
    type: 'interview',
    icon: 'VideoCamera',
    title: '安排了候选人面试',
    time: '1小时前'
  },
  {
    id: 4,
    type: 'assistant',
    icon: 'ChatDotRound',
    title: '使用AI助理查询了薪资政策',
    time: '2小时前'
  }
])

// 图表配置
const recruitmentChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '新增职位',
      type: 'line',
      data: [12, 19, 15, 22, 18, 25, 20],
      smooth: true,
      itemStyle: {
        color: '#409eff'
      }
    },
    {
      name: '简历投递',
      type: 'line',
      data: [45, 52, 38, 67, 55, 72, 58],
      smooth: true,
      itemStyle: {
        color: '#67c23a'
      }
    }
  ]
}))

const trainingChartOption = computed(() => ({
  tooltip: {
    trigger: 'item'
  },
  legend: {
    bottom: '0%'
  },
  series: [
    {
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 20,
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: [
        { value: 75, name: '已完成', itemStyle: { color: '#67c23a' } },
        { value: 15, name: '进行中', itemStyle: { color: '#e6a23c' } },
        { value: 10, name: '未开始', itemStyle: { color: '#f56c6c' } }
      ]
    }
  ]
}))

onMounted(() => {
  // 组件挂载后的初始化操作
})
</script>

<style lang="scss" scoped>
.dashboard {
  height: 100%;
  overflow-y: auto;
}

.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 32px;
  border-radius: 12px;
  margin-bottom: 24px;
  
  .welcome-content {
    .welcome-title {
      font-size: 28px;
      font-weight: 600;
      margin: 0 0 8px 0;
    }
    
    .welcome-subtitle {
      font-size: 16px;
      opacity: 0.9;
      margin: 0;
    }
  }
  
  .welcome-actions {
    display: flex;
    gap: 12px;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--border-lighter);
  
  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: white;
    
    &.recruitment { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    &.training { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    &.interview { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    &.assistant { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
  }
  
  .stat-content {
    flex: 1;
    
    .stat-value {
      font-size: 24px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 4px;
    }
    
    .stat-label {
      font-size: 14px;
      color: var(--text-secondary);
      margin-bottom: 8px;
    }
    
    .stat-change {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      
      &.positive { color: var(--success-color); }
      &.negative { color: var(--danger-color); }
    }
  }
}

.main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.quick-actions-card,
.recent-activities-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--border-lighter);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h3 {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.quick-action {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid var(--border-lighter);
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: var(--primary-color);
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
    transform: translateY(-2px);
  }
  
  .action-icon {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    color: white;
    
    &.recruitment { background: var(--primary-color); }
    &.training { background: var(--warning-color); }
    &.assistant { background: var(--success-color); }
  }
  
  .action-content {
    h4 {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 4px 0;
    }
    
    p {
      font-size: 12px;
      color: var(--text-secondary);
      margin: 0;
    }
  }
}

.activities-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .activity-icon {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    color: white;
    
    &.recruitment { background: var(--primary-color); }
    &.training { background: var(--warning-color); }
    &.interview { background: var(--info-color); }
    &.assistant { background: var(--success-color); }
  }
  
  .activity-content {
    flex: 1;
    
    .activity-title {
      font-size: 14px;
      color: var(--text-primary);
      margin-bottom: 2px;
    }
    
    .activity-time {
      font-size: 12px;
      color: var(--text-secondary);
    }
  }
}

.charts-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--border-lighter);
}

.chart-container {
  margin-top: 16px;
}

// 响应式设计
@media (max-width: 1200px) {
  .main-grid,
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .welcome-section {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .quick-actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>