<template>
  <div class="dashboard">
    <div class="page-container">
      <!-- 统一问答入口 -->
      <div class="qa-hero-section">
        <div class="qa-hero-content">
          <div class="hero-title">
            <el-icon class="hero-icon"><ChatDotRound /></el-icon>
            <h1>智能工作助手</h1>
          </div>
          <p class="hero-subtitle">
            用自然语言描述您的需求，系统将自动识别意图并跳转到对应功能
          </p>
          <div class="qa-input-container">
            <el-input
              v-model="qaText"
              class="qa-hero-input"
              size="large"
              placeholder="例如：帮我生成一个前端工程师的JD，或者根据知识库回答薪酬制度相关问题"
              clearable
              @keyup.enter="handleIntentSubmit"
            >
              <template #suffix>
                <el-button 
                  type="primary" 
                  :loading="qaLoading" 
                  @click="handleIntentSubmit"
                  class="qa-submit-btn"
                >
                  <el-icon><Search /></el-icon>
                  智能识别
                </el-button>
              </template>
            </el-input>
          </div>
          <div class="quick-examples">
            <span class="examples-label">快速示例：</span>
            <el-tag 
              v-for="example in quickExamples" 
              :key="example"
              class="example-tag"
              @click="useExample(example)"
            >
              {{ example }}
            </el-tag>
          </div>
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

            <div class="quick-action" @click="$router.push('/assistant/qa')">
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
          </div>
          <div class="chart-container">
            <v-chart :option="recruitmentChartOption" style="height: 300px" />
          </div>
        </div>

        <div class="chart-card">
          <div class="card-header">
            <h3>培训进度</h3>
          </div>
          <div class="chart-container">
            <v-chart :option="trainingChartOption" style="height: 300px" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { request } from '@/api'
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
import { Plus, ChatDotRound, UserFilled, Reading, VideoCamera, TrendCharts, Document, Files, EditPen, Search } from '@element-plus/icons-vue'

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

const router = useRouter()
const authStore = useAuthStore()

// 响应式数据
const chartPeriod = ref('30d')
const qaText = ref('')
const qaLoading = ref(false)

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

const quickExamples = ref([
  '生成前端工程师JD',
  '创建Java基础试卷',
  '制定面试方案',
  '查询薪酬制度'
])

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

const useExample = (example) => {
  qaText.value = example
}

const handleIntentSubmit = async () => {
  const text = (qaText.value || '').trim()
  if (!text) {
    ElMessage.warning('请输入您的需求')
    return
  }
  qaLoading.value = true
  try {
    const data = await request.post('/intent/route', { query: text })
    if (!data || !data.route) {
      throw new Error('意图解析失败')
    }
    const queryParams = { q: text }
    if (data.intent === 'kb_qa' && data.kb_id) {
      queryParams.kb_id = data.kb_id
    }
    router.push({ path: data.route, query: queryParams })
  } catch (err) {
    console.error(err)
    ElMessage.error('意图识别或跳转失败，请稍后重试')
  } finally {
    qaLoading.value = false
  }
}

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

.qa-hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 60px 40px;
  border-radius: 16px;
  margin-bottom: 32px;
  text-align: center;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 30% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 70% 80%, rgba(255, 255, 255, 0.08) 0%, transparent 50%);
    pointer-events: none;
  }

  .qa-hero-content {
    position: relative;
    z-index: 1;
    max-width: 800px;
    margin: 0 auto;

    .hero-title {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      margin-bottom: 16px;

      .hero-icon {
        font-size: 32px;
        color: rgba(255, 255, 255, 0.9);
      }

      h1 {
        font-size: 36px;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(45deg, #ffffff, #e8f4fd);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
    }

    .hero-subtitle {
      font-size: 18px;
      opacity: 0.9;
      margin: 0 0 32px 0;
      line-height: 1.6;
    }

    .qa-input-container {
      margin-bottom: 24px;

      .qa-hero-input {
        max-width: 600px;
        
        :deep(.el-input__wrapper) {
          border-radius: 50px;
          padding: 12px 20px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
          border: 2px solid rgba(255, 255, 255, 0.2);
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          
          &:hover, &.is-focus {
            border-color: rgba(255, 255, 255, 0.4);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
          }
        }

        :deep(.el-input__inner) {
          font-size: 16px;
          color: #333;
          
          &::placeholder {
            color: #999;
          }
        }

        .qa-submit-btn {
          border-radius: 25px;
          padding: 8px 20px;
          font-weight: 600;
          margin-right: 8px;
          background: linear-gradient(45deg, #4facfe, #00f2fe);
          border: none;
          
          &:hover {
            background: linear-gradient(45deg, #3d8bfe, #00d4fe);
            transform: translateY(-1px);
          }
        }
      }
    }

    .quick-examples {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      flex-wrap: wrap;

      .examples-label {
        font-size: 14px;
        opacity: 0.8;
        margin-right: 8px;
      }

      .example-tag {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover {
          background: rgba(255, 255, 255, 0.25);
          border-color: rgba(255, 255, 255, 0.5);
          transform: translateY(-2px);
        }
      }
    }
  }

  @media (max-width: 768px) {
    padding: 40px 20px;
    
    .qa-hero-content {
      .hero-title h1 {
        font-size: 28px;
      }
      
      .hero-subtitle {
        font-size: 16px;
      }
      
      .qa-input-container .qa-hero-input {
        max-width: 100%;
      }
      
      .quick-examples {
        flex-direction: column;
        align-items: stretch;
        
        .examples-label {
          margin-right: 0;
          margin-bottom: 8px;
        }
      }
    }
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