<template>
  <div class="knowledge-qa">
    <div class="page-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-content">
          <h1 class="page-title">
            <el-icon><ChatDotRound /></el-icon>
            知识问答
          </h1>
          <p class="page-subtitle">
            智能问答与知识检索一体化平台，快速获取专业解答
          </p>
        </div>
        <div class="header-actions">
          <el-button @click="clearChat">
            <el-icon><Delete /></el-icon>
            清空对话
          </el-button>
          <el-button type="primary" @click="refreshKnowledge">
            <el-icon><Refresh /></el-icon>
            刷新知识库
          </el-button>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <div class="main-content">
      <!-- 左侧对话区域 -->
      <div class="chat-panel">
        <el-card class="chat-card">
          <template #header>
            <div class="card-header">
              <el-icon><ChatDotRound /></el-icon>
              <span>智能对话</span>
              <el-badge :value="messages.length" class="message-count" />
            </div>
          </template>

          <!-- 聊天消息区域 -->
          <div class="chat-messages" ref="messagesContainer">
            <!-- 欢迎消息 -->
            <div class="welcome-message" v-if="messages.length === 0">
              <div class="welcome-content">
                <el-icon class="welcome-icon"><ChatDotRound /></el-icon>
                <h3>欢迎使用知识问答助手</h3>
                <p>我可以帮助您快速找到相关知识和专业解答</p>
                <div class="quick-questions">
                  <div 
                    v-for="question in quickQuestions"
                    :key="question.id"
                    class="quick-question"
                    @click="askQuickQuestion(question.text)"
                  >
                    <el-icon>
                      <component :is="question.icon" />
                    </el-icon>
                    <span>{{ question.text }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 消息列表 -->
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
                <el-avatar v-else :size="32" class="ai-avatar">
                  <el-icon><Robot /></el-icon>
                </el-avatar>
              </div>
              
              <div class="message-content">
                <div class="message-header">
                  <span class="message-sender">{{ message.type === 'user' ? '您' : 'AI助手' }}</span>
                  <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                </div>
                
                <div class="message-text" v-if="!message.thinking">
                  <div v-if="message.type === 'assistant' && message.thinking" class="thinking-indicator">
                    <el-icon class="rotating"><Loading /></el-icon>
                    <span>正在思考中...</span>
                  </div>
                  <div v-else v-html="formatMessage(message.content)"></div>
                </div>

                <!-- 相关文档引用 -->
                <div v-if="message.relatedDocs && message.relatedDocs.length > 0" class="related-docs">
                  <div class="docs-header">
                    <el-icon><Document /></el-icon>
                    <span>参考文档</span>
                  </div>
                  <div class="docs-list">
                    <div 
                      v-for="doc in message.relatedDocs"
                      :key="doc.id"
                      class="doc-item"
                      @click="highlightDocument(doc.id)"
                    >
                      <el-icon><Link /></el-icon>
                      <span>{{ doc.title }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 输入区域 -->
          <div class="chat-input">
            <div class="input-container">
              <el-input
                v-model="currentMessage"
                type="textarea"
                :rows="3"
                placeholder="请输入您的问题..."
                @keydown.ctrl.enter="sendMessage"
                @input="handleInputChange"
              />
              <div class="input-actions">
                <el-button 
                  type="primary" 
                  :disabled="!currentMessage.trim() || isThinking"
                  @click="sendMessage"
                >
                  <el-icon><Promotion /></el-icon>
                  发送 (Ctrl+Enter)
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右侧知识检索区域 -->
      <div class="knowledge-panel">
        <el-card class="knowledge-card">
          <template #header>
            <div class="card-header">
              <el-icon><Collection /></el-icon>
              <span>知识检索</span>
              <el-badge :value="filteredDocuments.length" class="doc-count" />
            </div>
          </template>

          <!-- 搜索区域 -->
          <div class="search-section">
            <el-input
              v-model="searchQuery"
              placeholder="搜索相关文档..."
              clearable
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <!-- 分类筛选 -->
          <div class="category-filter">
            <div class="filter-header">
              <span>文档分类</span>
              <el-button text @click="resetFilters">重置</el-button>
            </div>
            <div class="category-tags">
              <el-tag
                v-for="category in documentCategories"
                :key="category.key"
                :type="selectedCategory === category.key ? 'primary' : ''"
                :effect="selectedCategory === category.key ? 'dark' : 'plain'"
                @click="selectCategory(category.key)"
                class="category-tag"
              >
                <el-icon>
                  <component :is="category.icon" />
                </el-icon>
                {{ category.label }} ({{ category.count }})
              </el-tag>
            </div>
          </div>

          <!-- 文档列表 -->
          <div class="documents-list">
            <div class="list-header">
              <span>相关文档 ({{ filteredDocuments.length }})</span>
              <el-select v-model="sortBy" size="small" style="width: 120px">
                <el-option label="相关度" value="relevance" />
                <el-option label="时间" value="time" />
                <el-option label="热度" value="popularity" />
              </el-select>
            </div>
            
            <div class="documents-container">
              <div 
                v-for="doc in filteredDocuments"
                :key="doc.id"
                class="document-item"
                :class="{ 'highlighted': highlightedDocId === doc.id }"
                @click="selectDocument(doc)"
              >
                <div class="doc-header">
                  <div class="doc-title">{{ doc.title }}</div>
                  <div class="doc-meta">
                    <el-tag :type="getCategoryType(doc.category)" size="small">
                      {{ getCategoryLabel(doc.category) }}
                    </el-tag>
                    <span class="doc-score">{{ doc.relevanceScore }}%</span>
                  </div>
                </div>
                
                <div class="doc-summary">{{ doc.summary }}</div>
                
                <div class="doc-footer">
                  <div class="doc-stats">
                    <span><el-icon><View /></el-icon> {{ doc.views }}</span>
                    <span><el-icon><Star /></el-icon> {{ doc.rating }}</span>
                    <span><el-icon><Clock /></el-icon> {{ formatDate(doc.updateTime) }}</span>
                  </div>
                  <div class="doc-actions">
                    <el-button text size="small" @click.stop="previewDocument(doc)">
                      <el-icon><View /></el-icon>
                      预览
                    </el-button>
                    <el-button text size="small" @click.stop="insertDocReference(doc)">
                      <el-icon><Plus /></el-icon>
                      引用
                    </el-button>
                  </div>
                </div>
              </div>

              <!-- 空状态 -->
              <div v-if="filteredDocuments.length === 0" class="empty-state">
                <el-icon class="empty-icon"><DocumentRemove /></el-icon>
                <p>暂无相关文档</p>
                <el-button text @click="resetFilters">清除筛选条件</el-button>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 文档预览对话框 -->
    <el-dialog
      v-model="showDocPreview"
      :title="selectedDoc?.title"
      width="60%"
      :before-close="closeDocPreview"
    >
      <div v-if="selectedDoc" class="doc-preview">
        <div class="preview-header">
          <div class="doc-info">
            <el-tag :type="getCategoryType(selectedDoc.category)">
              {{ getCategoryLabel(selectedDoc.category) }}
            </el-tag>
            <span class="doc-author">作者：{{ selectedDoc.author }}</span>
            <span class="doc-date">更新时间：{{ formatDate(selectedDoc.updateTime) }}</span>
          </div>
        </div>
        <div class="preview-content" v-html="selectedDoc.content"></div>
      </div>
      
      <template #footer>
        <el-button @click="closeDocPreview">关闭</el-button>
        <el-button type="primary" @click="insertDocReference(selectedDoc)">
          引用到对话
        </el-button>
      </template>
    </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 响应式数据
const messages = ref([])
const currentMessage = ref('')
const isThinking = ref(false)
const messagesContainer = ref(null)

// 知识检索相关
const searchQuery = ref('')
const selectedCategory = ref('')
const sortBy = ref('relevance')
const highlightedDocId = ref(null)
const showDocPreview = ref(false)
const selectedDoc = ref(null)

// 快速问题
const quickQuestions = ref([
  {
    id: 1,
    text: '如何制定有效的招聘策略？',
    icon: 'UserFilled'
  },
  {
    id: 2,
    text: '员工绩效考核的最佳实践是什么？',
    icon: 'TrendCharts'
  },
  {
    id: 3,
    text: '如何设计员工培训计划？',
    icon: 'Reading'
  },
  {
    id: 4,
    text: '薪酬体系设计的关键要素有哪些？',
    icon: 'Money'
  }
])

// 文档分类
const documentCategories = ref([
  { key: '', label: '全部', icon: 'Collection', count: 0 },
  { key: 'recruitment', label: '招聘管理', icon: 'UserFilled', count: 0 },
  { key: 'performance', label: '绩效考核', icon: 'TrendCharts', count: 0 },
  { key: 'training', label: '培训发展', icon: 'Reading', count: 0 },
  { key: 'compensation', label: '薪酬福利', icon: 'Money', count: 0 },
  { key: 'policy', label: '政策制度', icon: 'Document', count: 0 }
])

// 模拟文档数据
const documents = ref([
  {
    id: 1,
    title: '现代企业招聘策略与实施指南',
    summary: '详细介绍了现代企业招聘的核心策略、流程设计和实施要点，包括人才画像、渠道选择、面试技巧等内容。',
    category: 'recruitment',
    author: '张三',
    updateTime: new Date('2024-01-15'),
    views: 1250,
    rating: 4.8,
    relevanceScore: 95,
    content: '<h3>招聘策略概述</h3><p>现代企业招聘需要系统性的策略规划...</p>'
  },
  {
    id: 2,
    title: '绩效考核体系设计与优化',
    summary: '从绩效管理理论到实践操作，全面解析如何构建科学有效的绩效考核体系。',
    category: 'performance',
    author: '李四',
    updateTime: new Date('2024-01-10'),
    views: 980,
    rating: 4.6,
    relevanceScore: 88,
    content: '<h3>绩效考核基础</h3><p>绩效考核是人力资源管理的核心环节...</p>'
  },
  {
    id: 3,
    title: '员工培训体系建设实务',
    summary: '涵盖培训需求分析、课程设计、实施管理和效果评估的完整培训体系建设方案。',
    category: 'training',
    author: '王五',
    updateTime: new Date('2024-01-08'),
    views: 756,
    rating: 4.7,
    relevanceScore: 82,
    content: '<h3>培训体系框架</h3><p>有效的培训体系应该包含以下几个关键要素...</p>'
  },
  {
    id: 4,
    title: '薪酬体系设计原理与方法',
    summary: '基于岗位价值评估的薪酬体系设计方法，包括薪酬结构、等级设置和激励机制。',
    category: 'compensation',
    author: '赵六',
    updateTime: new Date('2024-01-05'),
    views: 1100,
    rating: 4.9,
    relevanceScore: 90,
    content: '<h3>薪酬设计原则</h3><p>科学的薪酬体系设计需要遵循以下原则...</p>'
  },
  {
    id: 5,
    title: 'HR政策制度制定指南',
    summary: '企业人力资源政策制度的制定流程、要点分析和实施建议。',
    category: 'policy',
    author: '孙七',
    updateTime: new Date('2024-01-03'),
    views: 650,
    rating: 4.5,
    relevanceScore: 75,
    content: '<h3>政策制定流程</h3><p>HR政策制定需要经过以下几个阶段...</p>'
  }
])

// 计算属性
const filteredDocuments = computed(() => {
  let filtered = documents.value

  // 分类筛选
  if (selectedCategory.value) {
    filtered = filtered.filter(doc => doc.category === selectedCategory.value)
  }

  // 搜索筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(doc => 
      doc.title.toLowerCase().includes(query) ||
      doc.summary.toLowerCase().includes(query) ||
      doc.content.toLowerCase().includes(query)
    )
  }

  // 排序
  switch (sortBy.value) {
    case 'time':
      filtered.sort((a, b) => new Date(b.updateTime) - new Date(a.updateTime))
      break
    case 'popularity':
      filtered.sort((a, b) => b.views - a.views)
      break
    case 'relevance':
    default:
      filtered.sort((a, b) => b.relevanceScore - a.relevanceScore)
      break
  }

  return filtered
})

// 方法
const askQuickQuestion = (question) => {
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
  
  // 添加思考状态
  const thinkingMessage = {
    id: Date.now() + 1,
    type: 'assistant',
    thinking: true,
    timestamp: new Date()
  }
  
  messages.value.push(thinkingMessage)
  isThinking.value = true
  
  await nextTick()
  scrollToBottom()
  
  try {
    // 模拟AI思考时间
    await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 2000))
    
    // 移除思考消息
    messages.value.pop()
    
    // 生成回复和相关文档
    const response = await generateResponse(question)
    
    const assistantMessage = {
      id: Date.now() + 2,
      type: 'assistant',
      content: response.content,
      relatedDocs: response.relatedDocs,
      timestamp: new Date()
    }
    
    messages.value.push(assistantMessage)
    
    // 更新搜索查询以显示相关文档
    if (response.suggestedQuery) {
      searchQuery.value = response.suggestedQuery
    }
    
  } catch (error) {
    messages.value.pop()
    ElMessage.error('回复生成失败，请重试')
  } finally {
    isThinking.value = false
    await nextTick()
    scrollToBottom()
  }
}

const generateResponse = async (question) => {
  // 模拟AI回复生成
  const responses = [
    {
      content: '根据您的问题，我为您整理了相关的专业建议。现代企业招聘策略需要从多个维度进行考虑，包括人才需求分析、招聘渠道选择、面试流程设计等关键环节。',
      relatedDocs: [
        { id: 1, title: '现代企业招聘策略与实施指南' },
        { id: 4, title: '薪酬体系设计原理与方法' }
      ],
      suggestedQuery: '招聘策略'
    },
    {
      content: '绩效考核体系的设计需要遵循科学性、公平性和可操作性原则。建议从目标设定、指标选择、评估方法和结果应用四个方面进行系统规划。',
      relatedDocs: [
        { id: 2, title: '绩效考核体系设计与优化' }
      ],
      suggestedQuery: '绩效考核'
    }
  ]
  
  return responses[Math.floor(Math.random() * responses.length)]
}

const handleSearch = () => {
  // 搜索时重置高亮
  highlightedDocId.value = null
}

const selectCategory = (categoryKey) => {
  selectedCategory.value = selectedCategory.value === categoryKey ? '' : categoryKey
}

const resetFilters = () => {
  searchQuery.value = ''
  selectedCategory.value = ''
  highlightedDocId.value = null
}

const selectDocument = (doc) => {
  selectedDoc.value = doc
  showDocPreview.value = true
}

const previewDocument = (doc) => {
  selectDocument(doc)
}

const insertDocReference = (doc) => {
  const reference = `[参考文档：${doc.title}] `
  currentMessage.value = reference + currentMessage.value
  showDocPreview.value = false
  ElMessage.success('文档引用已添加到输入框')
}

const highlightDocument = (docId) => {
  highlightedDocId.value = docId
  // 滚动到对应文档
  const docElement = document.querySelector(`[data-doc-id="${docId}"]`)
  if (docElement) {
    docElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

const closeDocPreview = () => {
  showDocPreview.value = false
  selectedDoc.value = null
}

const clearChat = () => {
  messages.value = []
  ElMessage.success('对话已清空')
}

const refreshKnowledge = () => {
  // 模拟刷新知识库
  ElMessage.success('知识库已刷新')
}

const handleInputChange = () => {
  // 可以在这里添加输入提示等功能
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 工具方法
const formatTime = (date) => {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

const formatDate = (date) => {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(date)
}

const formatMessage = (content) => {
  // 简单的消息格式化
  return content.replace(/\n/g, '<br>')
}

const getCategoryType = (category) => {
  const types = {
    recruitment: 'primary',
    performance: 'success',
    training: 'warning',
    compensation: 'danger',
    policy: 'info'
  }
  return types[category] || ''
}

const getCategoryLabel = (category) => {
  const labels = {
    recruitment: '招聘管理',
    performance: '绩效考核',
    training: '培训发展',
    compensation: '薪酬福利',
    policy: '政策制度'
  }
  return labels[category] || '其他'
}

// 初始化
onMounted(() => {
  // 更新分类计数
  documentCategories.value.forEach(category => {
    if (category.key === '') {
      category.count = documents.value.length
    } else {
      category.count = documents.value.filter(doc => doc.category === category.key).length
    }
  })
})
</script>

<style scoped>
.knowledge-qa {
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.page-container {
  max-width: 1400px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 30px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.header-content {
  flex: 1;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title .el-icon {
  color: #409eff;
}

.page-subtitle {
  color: #606266;
  margin: 0;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.main-content {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 20px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.knowledge-panel {
  width: 400px;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-card,
.knowledge-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-card :deep(.el-card__body),
.knowledge-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.message-count,
.doc-count {
  margin-left: auto;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  margin-bottom: 16px;
}

.welcome-message {
  text-align: center;
  padding: 40px 20px;
}

.welcome-content {
  max-width: 400px;
  margin: 0 auto;
}

.welcome-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 16px;
}

.welcome-content h3 {
  margin: 0 0 8px 0;
  color: #303133;
}

.welcome-content p {
  color: #606266;
  margin: 0 0 24px 0;
}

.quick-questions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.quick-question {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.quick-question:hover {
  border-color: #409eff;
  background: #f0f9ff;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.ai-avatar {
  background: linear-gradient(135deg, #409eff, #67c23a);
}

.message-content {
  flex: 1;
  min-width: 0;
}

.user-message .message-content {
  text-align: right;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: #909399;
}

.user-message .message-header {
  flex-direction: row-reverse;
}

.message-sender {
  font-weight: 600;
}

.message-text {
  background: white;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  line-height: 1.6;
}

.user-message .message-text {
  background: #409eff;
  color: white;
}

.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-style: italic;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.related-docs {
  margin-top: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.docs-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
}

.docs-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.doc-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #409eff;
  transition: background 0.3s;
}

.doc-item:hover {
  background: #e6f7ff;
}

.chat-input {
  border-top: 1px solid #e4e7ed;
  padding-top: 16px;
}

.input-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
}

.search-section {
  margin-bottom: 20px;
}

.category-filter {
  margin-bottom: 20px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 600;
  color: #303133;
}

.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.category-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.category-tag .el-icon {
  margin-right: 4px;
}

.documents-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 600;
  color: #303133;
}

.documents-container {
  flex: 1;
  overflow-y: auto;
}

.document-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.document-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.document-item.highlighted {
  border-color: #409eff;
  background: #f0f9ff;
}

.doc-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.doc-title {
  font-weight: 600;
  color: #303133;
  flex: 1;
  margin-right: 12px;
}

.doc-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.doc-score {
  font-size: 12px;
  color: #67c23a;
  font-weight: 600;
}

.doc-summary {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 12px;
}

.doc-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.doc-stats {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}

.doc-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.doc-actions {
  display: flex;
  gap: 8px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.doc-preview {
  max-height: 60vh;
  overflow-y: auto;
}

.preview-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.doc-info {
  display: flex;
  gap: 16px;
  align-items: center;
  font-size: 14px;
  color: #606266;
}

.preview-content {
  line-height: 1.8;
}

.preview-content :deep(h3) {
  color: #303133;
  margin: 20px 0 12px 0;
}

.preview-content :deep(p) {
  margin: 12px 0;
  color: #606266;
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar,
.documents-container::-webkit-scrollbar,
.doc-preview::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track,
.documents-container::-webkit-scrollbar-track,
.doc-preview::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb,
.documents-container::-webkit-scrollbar-thumb,
.doc-preview::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover,
.documents-container::-webkit-scrollbar-thumb:hover,
.doc-preview::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .knowledge-panel {
    width: 350px;
  }
}

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .knowledge-panel {
    width: 100%;
    height: 300px;
  }
  
  .quick-questions {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>