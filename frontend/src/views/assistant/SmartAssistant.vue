<template>
  <div class="smart-assistant">
    <div class="page-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-content">
          <h1 class="page-title">
            <el-icon><ChatDotRound /></el-icon>
            智能助理
          </h1>
          <p class="page-subtitle">
            基于知识库的智能问答系统，为您提供专业的HR咨询服务
          </p>
        </div>
        <div class="header-actions">
          <el-button @click="clearHistory">
            <el-icon><Delete /></el-icon>
            清空对话
          </el-button>
          <el-button type="primary" @click="showKnowledgePanel = !showKnowledgePanel">
            <el-icon><Collection /></el-icon>
            {{ showKnowledgePanel ? '隐藏' : '显示' }}知识库
          </el-button>
        </div>
      </div>

      <div class="content-layout">
        <!-- 左侧知识库面板 -->
        <div v-if="showKnowledgePanel" class="knowledge-panel">
          <el-card class="knowledge-card">
            <template #header>
              <div class="card-header">
                <el-icon><Collection /></el-icon>
                <span>知识库检索</span>
              </div>
            </template>

            <div class="search-section">
              <el-input
                v-model="knowledgeQuery"
                placeholder="搜索知识库..."
                clearable
                @input="searchKnowledge"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>

            <div class="knowledge-categories">
              <h4>知识分类</h4>
              <div class="category-list">
                <div 
                  v-for="category in knowledgeCategories"
                  :key="category.key"
                  class="category-item"
                  :class="{ active: selectedCategory === category.key }"
                  @click="selectCategory(category.key)"
                >
                  <el-icon>
                    <component :is="category.icon" />
                  </el-icon>
                  <span>{{ category.label }}</span>
                  <el-badge :value="category.count" class="category-badge" />
                </div>
              </div>
            </div>

            <div class="knowledge-results">
              <h4>相关知识点</h4>
              <div class="results-list">
                <div 
                  v-for="item in filteredKnowledgeItems"
                  :key="item.id"
                  class="knowledge-item"
                  @click="insertKnowledge(item)"
                >
                  <div class="item-header">
                    <span class="item-title">{{ item.title }}</span>
                    <el-tag :type="getDifficultyType(item.difficulty)" size="small">
                      {{ getDifficultyLabel(item.difficulty) }}
                    </el-tag>
                  </div>
                  <p class="item-summary">{{ item.summary }}</p>
                  <div class="item-meta">
                    <span><el-icon><View /></el-icon> {{ item.views }}</span>
                    <span><el-icon><Star /></el-icon> {{ item.rating }}</span>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </div>

        <!-- 主聊天区域 -->
        <div class="chat-area">
          <el-card class="chat-card">
            <!-- 聊天消息区域 -->
            <div class="chat-messages" ref="messagesContainer">
              <div class="welcome-message" v-if="messages.length === 0">
                <div class="welcome-content">
                  <el-icon class="welcome-icon"><ChatDotRound /></el-icon>
                  <h3>欢迎使用HR智能助理</h3>
                  <p>我可以帮助您解答以下问题：</p>
                  <div class="suggestion-cards">
                    <div 
                      v-for="suggestion in quickSuggestions"
                      :key="suggestion.id"
                      class="suggestion-card"
                      @click="sendQuickQuestion(suggestion.question)"
                    >
                      <el-icon>
                        <component :is="suggestion.icon" />
                      </el-icon>
                      <span>{{ suggestion.title }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div 
                v-for="message in messages"
                :key="message.id"
                class="message-item"
                :class="{ 'user-message': message.type === 'user', 'assistant-message': message.type === 'assistant' }"
              >
                <div class="message-avatar">
                  <el-avatar v-if="message.type === 'user'" :size="32">
                    <el-icon><User /></el-icon>
                  </el-avatar>
                  <el-avatar v-else :size="32" class="assistant-avatar">
                    <el-icon><Robot /></el-icon>
                  </el-avatar>
                </div>
                
                <div class="message-content">
                  <div class="message-header">
                    <span class="message-sender">
                      {{ message.type === 'user' ? '您' : 'HR助理' }}
                    </span>
                    <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                  </div>
                  
                  <div class="message-body">
                    <div v-if="message.type === 'assistant' && message.thinking" class="thinking-indicator">
                      <el-icon class="thinking-icon"><Loading /></el-icon>
                      <span>正在思考...</span>
                    </div>
                    
                    <div v-else class="message-text" v-html="formatMessage(message.content)"></div>
                    
                    <!-- 知识来源 -->
                    <div v-if="message.sources && message.sources.length > 0" class="message-sources">
                      <div class="sources-header">
                        <el-icon><Link /></el-icon>
                        <span>参考来源</span>
                      </div>
                      <div class="sources-list">
                        <div 
                          v-for="source in message.sources"
                          :key="source.id"
                          class="source-item"
                          @click="viewSource(source)"
                        >
                          <el-icon><Document /></el-icon>
                          <span>{{ source.title }}</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- 相关问题推荐 -->
                    <div v-if="message.relatedQuestions && message.relatedQuestions.length > 0" class="related-questions">
                      <div class="questions-header">
                        <el-icon><QuestionFilled /></el-icon>
                        <span>相关问题</span>
                      </div>
                      <div class="questions-list">
                        <el-button 
                          v-for="question in message.relatedQuestions"
                          :key="question"
                          size="small"
                          text
                          @click="sendQuickQuestion(question)"
                        >
                          {{ question }}
                        </el-button>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 消息操作 -->
                  <div v-if="message.type === 'assistant'" class="message-actions">
                    <el-button size="small" text @click="copyMessage(message.content)">
                      <el-icon><CopyDocument /></el-icon>
                      复制
                    </el-button>
                    <el-button size="small" text @click="likeMessage(message)">
                      <el-icon><Like /></el-icon>
                      有用
                    </el-button>
                    <el-button size="small" text @click="dislikeMessage(message)">
                      <el-icon><Dislike /></el-icon>
                      无用
                    </el-button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 输入区域 -->
            <div class="chat-input">
              <div class="input-toolbar">
                <el-button size="small" text @click="showTemplates = !showTemplates">
                  <el-icon><Menu /></el-icon>
                  常用模板
                </el-button>
                <el-button size="small" text @click="uploadFile">
                  <el-icon><Paperclip /></el-icon>
                  上传文件
                </el-button>
              </div>
              
              <!-- 常用模板 -->
              <div v-if="showTemplates" class="templates-panel">
                <div class="templates-grid">
                  <div 
                    v-for="template in messageTemplates"
                    :key="template.id"
                    class="template-item"
                    @click="useTemplate(template)"
                  >
                    <div class="template-title">{{ template.title }}</div>
                    <div class="template-content">{{ template.content }}</div>
                  </div>
                </div>
              </div>
              
              <div class="input-container">
                <el-input
                  v-model="currentMessage"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入您的问题..."
                  @keydown.enter.ctrl="sendMessage"
                  @keydown.enter.meta="sendMessage"
                  resize="none"
                />
                <div class="input-actions">
                  <div class="input-tips">
                    <span>Ctrl + Enter 发送</span>
                  </div>
                  <el-button 
                    type="primary" 
                    @click="sendMessage"
                    :loading="isThinking"
                    :disabled="!currentMessage.trim()"
                  >
                    <el-icon><Promotion /></el-icon>
                    {{ isThinking ? '思考中...' : '发送' }}
                  </el-button>
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 响应式数据
const showKnowledgePanel = ref(true)
const knowledgeQuery = ref('')
const selectedCategory = ref('')
const currentMessage = ref('')
const isThinking = ref(false)
const showTemplates = ref(false)
const messagesContainer = ref()

// 消息列表
const messages = ref([])

// 知识库分类
const knowledgeCategories = [
  { key: 'recruitment', label: '招聘管理', icon: 'UserFilled', count: 45 },
  { key: 'training', label: '培训发展', icon: 'Reading', count: 38 },
  { key: 'performance', label: '绩效管理', icon: 'TrendCharts', count: 32 },
  { key: 'compensation', label: '薪酬福利', icon: 'Money', count: 28 },
  { key: 'policy', label: '政策法规', icon: 'Document', count: 56 },
  { key: 'culture', label: '企业文化', icon: 'Star', count: 24 }
]

// 快速建议
const quickSuggestions = [
  {
    id: 1,
    title: '招聘流程',
    question: '请介绍一下标准的招聘流程',
    icon: 'UserFilled'
  },
  {
    id: 2,
    title: '绩效考核',
    question: '如何设计有效的绩效考核体系？',
    icon: 'TrendCharts'
  },
  {
    id: 3,
    title: '员工培训',
    question: '新员工培训应该包含哪些内容？',
    icon: 'Reading'
  },
  {
    id: 4,
    title: '薪酬设计',
    question: '如何设计公平合理的薪酬体系？',
    icon: 'Money'
  }
]

// 消息模板
const messageTemplates = [
  {
    id: 1,
    title: '招聘需求分析',
    content: '我需要为[职位名称]制定招聘计划，请帮我分析岗位需求和招聘策略。'
  },
  {
    id: 2,
    title: '面试问题设计',
    content: '请为[职位名称]设计一套面试问题，包括技能评估和文化匹配度测试。'
  },
  {
    id: 3,
    title: '培训方案制定',
    content: '我需要为[部门/岗位]制定培训方案，请提供详细的培训计划和实施建议。'
  },
  {
    id: 4,
    title: '政策咨询',
    content: '关于[具体政策问题]，请提供相关的法律法规依据和实施建议。'
  }
]

// 模拟知识库数据
const knowledgeItems = ref([
  {
    id: 1,
    title: '招聘流程标准化指南',
    summary: '详细介绍企业招聘的标准流程和最佳实践',
    category: 'recruitment',
    difficulty: 'intermediate',
    views: 1250,
    rating: 4.8
  },
  {
    id: 2,
    title: '绩效管理体系设计',
    summary: '如何构建科学有效的绩效管理体系',
    category: 'performance',
    difficulty: 'advanced',
    views: 980,
    rating: 4.9
  },
  {
    id: 3,
    title: '员工培训与发展',
    summary: '员工培训计划的制定和实施方法',
    category: 'training',
    difficulty: 'beginner',
    views: 1580,
    rating: 4.7
  }
])

// 计算属性
const filteredKnowledgeItems = computed(() => {
  return knowledgeItems.value.filter(item => {
    const matchesQuery = !knowledgeQuery.value || 
      item.title.toLowerCase().includes(knowledgeQuery.value.toLowerCase()) ||
      item.summary.toLowerCase().includes(knowledgeQuery.value.toLowerCase())
    
    const matchesCategory = !selectedCategory.value || item.category === selectedCategory.value
    
    return matchesQuery && matchesCategory
  })
})

// 方法
const searchKnowledge = () => {
  // 搜索逻辑已在计算属性中实现
}

const selectCategory = (category) => {
  selectedCategory.value = selectedCategory.value === category ? '' : category
}

const getDifficultyType = (difficulty) => {
  const types = {
    beginner: 'success',
    intermediate: 'warning',
    advanced: 'danger'
  }
  return types[difficulty] || ''
}

const getDifficultyLabel = (difficulty) => {
  const labels = {
    beginner: '初级',
    intermediate: '中级',
    advanced: '高级'
  }
  return labels[difficulty] || difficulty
}

const insertKnowledge = (item) => {
  currentMessage.value += `请参考"${item.title}"相关内容，`
}

const sendQuickQuestion = (question) => {
  currentMessage.value = question
  sendMessage()
}

const sendMessage = async () => {
  if (!currentMessage.value.trim() || isThinking.value) return
  
  const userMessage = {
    id: Date.now(),
    type: 'user',
    content: currentMessage.value,
    timestamp: new Date()
  }
  
  messages.value.push(userMessage)
  
  const question = currentMessage.value
  currentMessage.value = ''
  showTemplates.value = false
  
  // 添加思考中的消息
  const thinkingMessage = {
    id: Date.now() + 1,
    type: 'assistant',
    content: '',
    thinking: true,
    timestamp: new Date()
  }
  
  messages.value.push(thinkingMessage)
  isThinking.value = true
  
  await nextTick()
  scrollToBottom()
  
  try {
    // 模拟AI思考时间
    await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 2000))
    
    // 移除思考消息
    messages.value.pop()
    
    // 生成回复
    const response = await generateResponse(question)
    
    const assistantMessage = {
      id: Date.now() + 2,
      type: 'assistant',
      content: response.content,
      sources: response.sources,
      relatedQuestions: response.relatedQuestions,
      timestamp: new Date()
    }
    
    messages.value.push(assistantMessage)
    
  } catch (error) {
    messages.value.pop() // 移除思考消息
    ElMessage.error('回复生成失败，请重试')
  } finally {
    isThinking.value = false
    await nextTick()
    scrollToBottom()
  }
}

const generateResponse = async (question) => {
  // 模拟AI回复生成
  const responses = {
    '请介绍一下标准的招聘流程': {
      content: `标准的招聘流程通常包括以下几个关键步骤：

**1. 需求分析与岗位设计**
- 明确招聘需求和岗位要求
- 制定岗位说明书和任职资格

**2. 招聘计划制定**
- 确定招聘渠道和时间安排
- 制定招聘预算和资源配置

**3. 简历筛选**
- 根据岗位要求筛选合适候选人
- 进行初步背景调查

**4. 面试评估**
- 安排多轮面试（HR面试、技术面试、管理层面试）
- 使用结构化面试方法

**5. 录用决策**
- 综合评估候选人表现
- 进行背景调查和体检

**6. 入职安排**
- 发送录用通知和合同
- 安排入职培训和工作交接

这个流程可以根据企业规模和岗位特点进行调整优化。`,
      sources: [
        { id: 1, title: '招聘流程标准化指南' },
        { id: 2, title: 'HR最佳实践手册' }
      ],
      relatedQuestions: [
        '如何提高招聘效率？',
        '面试中应该注意哪些问题？',
        '如何评估候选人的文化匹配度？'
      ]
    }
  }
  
  const defaultResponse = {
    content: `感谢您的问题。基于我的知识库，我为您提供以下建议：

这是一个很好的问题，涉及到HR管理的核心内容。根据最佳实践和行业标准，我建议您可以从以下几个方面来考虑：

1. **理论基础**：首先了解相关的理论框架和基本概念
2. **实践应用**：结合企业实际情况制定具体的实施方案
3. **持续优化**：建立反馈机制，不断改进和完善

如果您需要更具体的指导，请提供更多的背景信息，我会为您提供更详细的建议。`,
    sources: [
      { id: 1, title: 'HR管理实务指南' },
      { id: 2, title: '人力资源最佳实践' }
    ],
    relatedQuestions: [
      '如何制定实施计划？',
      '有哪些常见的挑战？',
      '如何衡量效果？'
    ]
  }
  
  return responses[question] || defaultResponse
}

const formatMessage = (content) => {
  // 简单的markdown格式化
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}

const formatTime = (timestamp) => {
  const now = new Date()
  const diff = now - timestamp
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  
  return timestamp.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const clearHistory = () => {
  messages.value = []
  ElMessage.success('对话历史已清空')
}

const copyMessage = (content) => {
  navigator.clipboard.writeText(content.replace(/<[^>]*>/g, ''))
  ElMessage.success('内容已复制到剪贴板')
}

const likeMessage = (message) => {
  ElMessage.success('感谢您的反馈')
}

const dislikeMessage = (message) => {
  ElMessage.info('我们会继续改进回答质量')
}

const viewSource = (source) => {
  ElMessage.info(`查看来源：${source.title}`)
}

const useTemplate = (template) => {
  currentMessage.value = template.content
  showTemplates.value = false
}

const uploadFile = () => {
  ElMessage.info('文件上传功能开发中')
}

onMounted(() => {
  // 初始化
})
</script>

<style lang="scss" scoped>
.smart-assistant {
  height: 100%;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 20px;
}

.page-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  
  .header-content {
    .page-title {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 28px;
      font-weight: 700;
      background: linear-gradient(135deg, #667eea, #764ba2);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0 0 8px 0;
      
      .el-icon {
        font-size: 32px;
        color: #667eea;
      }
    }
    
    .page-subtitle {
      color: #64748b;
      margin: 0;
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

.content-layout {
  display: flex;
  gap: 24px;
  height: calc(100vh - 200px);
}

.knowledge-panel {
  width: 350px;
  flex-shrink: 0;
  
  .knowledge-card {
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
      
      .card-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        color: #1e293b;
        
        .el-icon {
          font-size: 18px;
          color: #667eea;
        }
      }
    }
    
    :deep(.el-card__body) {
      padding: 20px;
      height: calc(100% - 60px);
      overflow-y: auto;
    }
  }
  
  .search-section {
    margin-bottom: 20px;
    
    :deep(.el-input__wrapper) {
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      transition: all 0.3s ease;
      
      &:hover {
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
      }
      
      &.is-focus {
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
      }
    }
  }
  
  .knowledge-list {
    .knowledge-item {
      padding: 16px;
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(248, 250, 252, 0.9));
      border: 1px solid rgba(226, 232, 240, 0.5);
      border-radius: 12px;
      margin-bottom: 12px;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        border-color: rgba(102, 126, 234, 0.3);
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15);
        transform: translateY(-2px);
      }
      
      .item-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 8px;
        
        .item-title {
          font-weight: 600;
          color: #1e293b;
          font-size: 14px;
          line-height: 1.4;
        }
        
        .el-tag {
          border-radius: 8px;
          font-size: 11px;
          font-weight: 500;
          
          &.el-tag--success {
            background: linear-gradient(135deg, #10b981, #059669);
            border: none;
            color: white;
          }
          
          &.el-tag--warning {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            border: none;
            color: white;
          }
          
          &.el-tag--danger {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            border: none;
            color: white;
          }
        }
      }
      
      .item-summary {
        color: #64748b;
        font-size: 12px;
        line-height: 1.5;
        margin: 0 0 8px 0;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
      
      .item-meta {
        display: flex;
        gap: 12px;
        font-size: 11px;
        color: #94a3b8;
        
        span {
          display: flex;
          align-items: center;
          gap: 4px;
          
          .el-icon {
            font-size: 12px;
          }
        }
      }
    }
  }
}

.chat-area {
  flex: 1;
  
  .chat-card {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    
    :deep(.el-card__body) {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 0;
    }
  }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  
  .welcome-message {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    
    .welcome-content {
      text-align: center;
      max-width: 600px;
      
      .welcome-icon {
        font-size: 64px;
        color: #667eea;
        margin-bottom: 24px;
      }
      
      h3 {
        font-size: 24px;
        font-weight: 700;
        color: #1e293b;
        margin: 0 0 12px 0;
      }
      
      p {
        color: #64748b;
        font-size: 16px;
        margin: 0 0 32px 0;
      }
      
      .suggestion-cards {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        
        .suggestion-card {
          padding: 20px;
          background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
          border: 1px solid rgba(102, 126, 234, 0.2);
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.3s ease;
          text-align: left;
          
          &:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
            border-color: rgba(102, 126, 234, 0.4);
          }
          
          .el-icon {
            font-size: 24px;
            color: #667eea;
            margin-bottom: 12px;
          }
          
          .suggestion-title {
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 8px;
            font-size: 16px;
          }
          
          .suggestion-text {
            color: #64748b;
            font-size: 14px;
            line-height: 1.5;
          }
        }
      }
    }
  }
  
  .message-item {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
    
    &.user-message {
      flex-direction: row-reverse;
      
      .message-content {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 16px 16px 4px 16px;
      }
    }
    
    &.assistant-message {
      .message-content {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(248, 250, 252, 0.9));
        border: 1px solid rgba(226, 232, 240, 0.5);
        border-radius: 16px 16px 16px 4px;
      }
    }
    
    .message-avatar {
      flex-shrink: 0;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .assistant-avatar {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        font-size: 18px;
      }
      
      .user-avatar {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        font-size: 18px;
      }
    }
    
    .message-content {
      flex: 1;
      max-width: 70%;
      padding: 16px 20px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      
      .message-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        
        .message-sender {
          font-weight: 600;
          font-size: 12px;
          color: #64748b;
        }
        
        .message-time {
          font-size: 11px;
          opacity: 0.7;
        }
      }
      
      .message-body {
        .thinking-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #64748b;
          
          .thinking-icon {
            animation: rotate 1s linear infinite;
            color: #667eea;
          }
        }
        
        .message-text {
          line-height: 1.6;
          color: #374151;
          
          :deep(strong) {
            font-weight: 600;
            color: #1e293b;
          }
          
          :deep(em) {
            font-style: italic;
            color: #667eea;
          }
          
          :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
            color: #1e293b;
            margin: 16px 0 8px 0;
          }
          
          :deep(ul), :deep(ol) {
            margin: 8px 0;
            padding-left: 20px;
          }
          
          :deep(li) {
            margin: 4px 0;
          }
        }
        
        .message-sources {
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid rgba(226, 232, 240, 0.5);
          
          .sources-header {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: #64748b;
            margin-bottom: 8px;
            font-weight: 600;
            
            .el-icon {
              color: #667eea;
            }
          }
          
          .sources-list {
            .source-item {
              display: flex;
              align-items: center;
              gap: 8px;
              padding: 8px 12px;
              border-radius: 8px;
              cursor: pointer;
              font-size: 12px;
              color: #667eea;
              background: rgba(102, 126, 234, 0.05);
              border: 1px solid rgba(102, 126, 234, 0.1);
              margin-bottom: 4px;
              transition: all 0.3s ease;
              
              &:hover {
                background: rgba(102, 126, 234, 0.1);
                border-color: rgba(102, 126, 234, 0.2);
                transform: translateX(4px);
              }
              
              .el-icon {
                font-size: 14px;
              }
            }
          }
        }
        
        .related-questions {
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid rgba(226, 232, 240, 0.5);
          
          .questions-header {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: #64748b;
            margin-bottom: 12px;
            font-weight: 600;
            
            .el-icon {
              color: #667eea;
            }
          }
          
          .questions-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            
            .el-button {
              border-radius: 8px;
              font-size: 12px;
              padding: 6px 12px;
              background: rgba(102, 126, 234, 0.05);
              border: 1px solid rgba(102, 126, 234, 0.2);
              color: #667eea;
              
              &:hover {
                background: rgba(102, 126, 234, 0.1);
                border-color: rgba(102, 126, 234, 0.3);
                transform: translateY(-1px);
              }
            }
          }
        }
      }
      
      .message-actions {
        margin-top: 12px;
        display: flex;
        gap: 8px;
        opacity: 0;
        transition: opacity 0.3s ease;
        
        .el-button {
          font-size: 12px;
          padding: 4px 8px;
          border-radius: 6px;
          
          &:hover {
            transform: translateY(-1px);
          }
        }
      }
    }
    
    &:hover .message-actions {
      opacity: 1;
    }
  }
}

.chat-input {
  border-top: 1px solid rgba(226, 232, 240, 0.5);
  padding: 20px;
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.9), rgba(255, 255, 255, 0.9));
  border-radius: 0 0 16px 16px;
  
  .input-toolbar {
    display: flex;
    gap: 12px;
    margin-bottom: 12px;
    
    .el-button {
      font-size: 12px;
      padding: 6px 12px;
      border-radius: 8px;
      background: rgba(102, 126, 234, 0.05);
      border: 1px solid rgba(102, 126, 234, 0.2);
      color: #667eea;
      
      &:hover {
        background: rgba(102, 126, 234, 0.1);
        border-color: rgba(102, 126, 234, 0.3);
        transform: translateY(-1px);
      }
    }
  }
  
  .templates-panel {
    margin-bottom: 16px;
    padding: 16px;
    background: rgba(255, 255, 255, 0.8);
    border: 1px solid rgba(226, 232, 240, 0.5);
    border-radius: 12px;
    backdrop-filter: blur(5px);
    
    .templates-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
      
      .template-item {
        padding: 12px 16px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(248, 250, 252, 0.9));
        border: 1px solid rgba(226, 232, 240, 0.5);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover {
          border-color: rgba(102, 126, 234, 0.3);
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
        }
        
        .template-title {
          font-weight: 600;
          font-size: 13px;
          color: #1e293b;
          margin-bottom: 6px;
        }
        
        .template-content {
          font-size: 12px;
          color: #64748b;
          line-height: 1.4;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      }
    }
  }
  
  .input-container {
    position: relative;
    
    :deep(.el-textarea__inner) {
      border-radius: 12px;
      border: 1px solid rgba(226, 232, 240, 0.8);
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(5px);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      transition: all 0.3s ease;
      resize: none;
      
      &:hover {
        border-color: rgba(102, 126, 234, 0.3);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
      }
      
      &:focus {
        border-color: rgba(102, 126, 234, 0.5);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
      }
    }
    
    .input-actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 12px;
      
      .input-tips {
        font-size: 12px;
        color: #94a3b8;
      }
      
      .el-button {
        border-radius: 10px;
        font-weight: 600;
        padding: 10px 20px;
        
        &.el-button--primary {
          background: linear-gradient(135deg, #667eea, #764ba2);
          border: none;
          
          &:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
          }
          
          &:disabled {
            background: #94a3b8;
            transform: none;
            box-shadow: none;
          }
        }
      }
    }
  }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// 响应式设计
@media (max-width: 1200px) {
  .smart-assistant {
    padding: 12px;
  }
  
  .content-layout {
    flex-direction: column;
    height: auto;
  }
  
  .knowledge-panel {
    width: 100%;
    order: 2;
    
    .knowledge-card {
      height: 300px;
    }
  }
  
  .chat-area {
    order: 1;
    height: 500px;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    padding: 20px;
    
    .header-actions {
      width: 100%;
      justify-content: center;
    }
  }
  
  .welcome-content .suggestion-cards {
    grid-template-columns: 1fr;
  }
  
  .message-item .message-content {
    max-width: 85%;
  }
  
  .templates-grid {
    grid-template-columns: 1fr !important;
  }
  
  .knowledge-panel {
    .knowledge-card {
      height: 250px;
    }
  }
  
  .chat-area {
    height: 400px;
  }
}

@media (max-width: 480px) {
  .smart-assistant {
    padding: 8px;
  }
  
  .page-header {
    padding: 16px;
    
    .page-title {
      font-size: 24px !important;
    }
  }
  
  .chat-input {
    padding: 16px;
  }
  
  .message-item {
    .message-content {
      max-width: 90%;
      padding: 12px 16px;
    }
  }
}
</style>