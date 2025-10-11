<template>
  <div class="exam-generator">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><EditPen /></el-icon>
          智能试卷生成
        </h1>
        <p class="page-subtitle">基于知识库自动生成专业考试试卷</p>
      </div>
      <div class="header-actions">
        <el-button @click="createNewExam" type="primary">
          <el-icon><Plus /></el-icon>
          新建试卷
        </el-button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧试卷列表 -->
      <div class="exam-list-panel">
        <div class="list-header">
          <h3>试卷列表 ({{ savedExams.length }})</h3>
          <el-button size="small" @click="refreshExamList">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
        
        <div class="exam-list-content">
          <div v-if="examListLoading" class="loading-state">
            <el-icon><Loading /></el-icon>
            <span>加载中...</span>
          </div>
          
          <div v-else-if="savedExams.length === 0" class="empty-state">
            <el-icon><Document /></el-icon>
            <p class="empty-text">暂无试卷数据</p>
          </div>
          
          <div v-else>
            <div
              v-for="exam in savedExams"
              :key="exam.id"
              :class="['list-card', { selected: selectedExam?.id === exam.id }]"
              @click="selectExam(exam)"
            >
              <div class="card-content">
                <h4 class="exam-title">{{ exam.name || '未命名试卷' }}</h4>
                <div class="exam-meta">
                  <span class="meta-item">
                    <el-icon><Clock /></el-icon>
                    {{ exam.duration }}分钟
                  </span>
                  <span class="meta-item">
                    <el-icon><Document /></el-icon>
                    {{ exam.totalQuestions }}题
                  </span>
                  <span class="meta-item">
                    <el-icon><Star /></el-icon>
                    {{ exam.totalScore }}分
                  </span>
                </div>
                <div class="exam-actions">
                  <el-button text size="small" @click.stop="editExam(exam)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-button>
                  <el-button text size="small" @click.stop="duplicateExam(exam)">
                    <el-icon><DocumentCopy /></el-icon>
                    复制
                  </el-button>
                  <el-button text size="small" @click.stop="previewExam(exam)">
                    <el-icon><View /></el-icon>
                    预览
                  </el-button>
                  <el-button text size="small" type="danger" @click.stop="deleteExam(exam)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧编辑区域 -->
      <div class="editor-content">
        <!-- 欢迎页面 -->
        <div v-if="!showExamEditor" class="welcome-content">
          <el-icon class="welcome-icon"><EditPen /></el-icon>
          <h2 class="welcome-title">欢迎使用智能试卷生成</h2>
          <p class="welcome-subtitle">选择左侧的试卷进行编辑，或创建新的试卷</p>
        </div>

        <!-- 试卷编辑区域 -->
        <div v-else class="exam-editor-content">
          <div class="editor-header">
            <div class="header-left">
              <el-button class="back-button" @click="showExamEditor = false">
                <el-icon><Back /></el-icon>
              </el-button>
              <h3 class="editor-title">{{ selectedExam ? '编辑试卷' : '创建新试卷' }}</h3>
            </div>
            <div class="header-actions">
              <el-button type="primary" @click="generateExam" :loading="generating">
                  <el-icon><Star /></el-icon>
                  {{ generating ? '生成中...' : '生成试卷' }}
                </el-button>
            </div>
          </div>

          <div class="editor-body">
            <div class="form-section">
              <h4 class="section-title">
                <el-icon><Setting /></el-icon>
                基本信息
              </h4>
              <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
                <el-row :gutter="16">
                  <el-col :span="12">
                    <el-form-item label="试卷名称" prop="examName">
                      <el-input v-model="form.examName" placeholder="请输入试卷名称" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="考试科目" prop="subject">
                      <el-select v-model="form.subject" placeholder="请选择考试科目">
                        <el-option label="前端开发" value="frontend" />
                        <el-option label="后端开发" value="backend" />
                        <el-option label="数据库" value="database" />
                        <el-option label="算法与数据结构" value="algorithm" />
                        <el-option label="系统设计" value="system" />
                        <el-option label="项目管理" value="management" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-row :gutter="16">
                  <el-col :span="8">
                    <el-form-item label="难度等级">
                      <el-select v-model="form.difficulty">
                        <el-option label="初级" value="easy" />
                        <el-option label="中级" value="medium" />
                        <el-option label="高级" value="hard" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="考试时长">
                      <el-input-number v-model="form.duration" :min="30" :max="180" :step="15" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="总分">
                      <el-input-number v-model="form.totalScore" :min="50" :max="200" :step="10" />
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </div>

            <div class="form-section">
              <h4 class="section-title">
                <el-icon><Document /></el-icon>
                题目配置
              </h4>
              <el-form-item label="题目类型" prop="questionTypes">
                <el-checkbox-group v-model="form.questionTypes">
                  <el-checkbox label="单选题">单选题</el-checkbox>
                  <el-checkbox label="多选题">多选题</el-checkbox>
                  <el-checkbox label="判断题">判断题</el-checkbox>
                  <el-checkbox label="填空题">填空题</el-checkbox>
                  <el-checkbox label="简答题">简答题</el-checkbox>
                  <el-checkbox label="编程题">编程题</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </div>

            <div class="form-section">
              <h4 class="section-title">
                <el-icon><Folder /></el-icon>
                知识库文件
              </h4>
              <div v-if="form.knowledgeFiles.length === 0" class="empty-state">
                <el-icon><Document /></el-icon>
                <p class="empty-text">暂未选择知识库文件</p>
                <el-button type="primary" @click="showKnowledgeDialog = true">选择文件</el-button>
              </div>
              <div v-else>
                <div v-for="file in form.knowledgeFiles" :key="file.id" class="file-item">
                  <el-icon><Document /></el-icon>
                  <span>{{ file.name }}</span>
                  <el-button text @click="removeKnowledgeFile(file.id)">
                    <el-icon><Close /></el-icon>
                  </el-button>
                </div>
                <el-button @click="showKnowledgeDialog = true">
                  <el-icon><Plus /></el-icon>
                  添加更多文件
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 知识库文件选择对话框 -->
    <el-dialog v-model="showKnowledgeDialog" title="选择知识库文件" width="800px">
      <div class="knowledge-selection-container">
        <!-- 知识库选择 -->
        <div class="knowledge-base-section">
          <h4>选择知识库</h4>
          <el-select 
            v-model="selectedKnowledgeBase" 
            placeholder="请选择知识库"
            @change="onKnowledgeBaseChange"
            style="width: 100%"
            :loading="knowledgeBasesLoading"
          >
            <el-option
              v-for="kb in knowledgeBases"
              :key="kb.id"
              :label="kb.name"
              :value="kb.id"
            />
          </el-select>
        </div>

        <!-- 文档列表 -->
        <div class="knowledge-documents-section" v-if="selectedKnowledgeBase">
          <h4>选择文档</h4>
          <div class="documents-search">
            <el-input
              v-model="documentSearchKeyword"
              placeholder="搜索文档..."
              @input="searchDocuments"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
          <div class="documents-list" v-loading="documentsLoading">
            <div v-if="knowledgeDocuments.length === 0" class="empty-documents">
              <p>该知识库暂无文档</p>
            </div>
            <div v-else>
              <div v-for="doc in knowledgeDocuments" :key="doc.id" class="document-item">
                <el-checkbox 
                  :model-value="selectedKnowledgeFiles.includes(doc.id)"
                  @change="toggleKnowledgeFile(doc.id)"
                >
                  <div class="document-info">
                    <div class="document-name">{{ doc.filename || doc.original_filename }}</div>
                    <div class="document-meta">
                      <span class="file-size">{{ formatFileSize(doc.file_size) }}</span>
                      <span class="file-type">{{ doc.mime_type }}</span>
                    </div>
                  </div>
                </el-checkbox>
              </div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showKnowledgeDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmKnowledgeFiles" :disabled="selectedKnowledgeFiles.length === 0">
          确认选择 ({{ selectedKnowledgeFiles.length }})
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  EditPen, Plus, Refresh, Document, Clock, Star, Edit, DocumentCopy, 
  View, Delete, Back, Loading, Setting, Folder, Close, Search
} from '@element-plus/icons-vue'
import { examApi } from '@/api/exam'

// 响应式数据
const formRef = ref()
const generating = ref(false)
const generatedExam = ref(null)
const examListLoading = ref(false)
const searchKeyword = ref('')

// 试卷列表数据
const savedExams = ref([])
const selectedExam = ref(null)
const showExamEditor = ref(false)

// 知识库文件相关
const showKnowledgeDialog = ref(false)
const knowledgeFiles = ref([])
const selectedKnowledgeFiles = ref([])

// 知识库选择相关
const knowledgeBases = ref([])
const selectedKnowledgeBase = ref('')
const knowledgeBasesLoading = ref(false)
const knowledgeDocuments = ref([])
const documentsLoading = ref(false)
const documentSearchKeyword = ref('')

// 表单数据
const form = reactive({
  examName: '',
  subject: '',
  difficulty: 'medium',
  duration: 90,
  totalScore: 100,
  questionTypes: ['单选题', '多选题'],
  questionCounts: {
    single: 10,
    multiple: 5,
    judge: 5,
    fill: 3,
    short: 2,
    coding: 1
  },
  knowledgeFiles: [],
  specialRequirements: ''
})

// 表单验证规则
const rules = {
  examName: [
    { required: true, message: '请输入试卷名称', trigger: 'blur' }
  ],
  subject: [
    { required: true, message: '请选择考试科目', trigger: 'change' }
  ],
  questionTypes: [
    { required: true, message: '请至少选择一种题目类型', trigger: 'change' }
  ]
}

// API调用方法
const fetchExamList = async () => {
  try {
    examListLoading.value = true
    const response = await examApi.getExamList()
    savedExams.value = response.data || []
  } catch (error) {
    console.error('获取试卷列表失败:', error)
    ElMessage.error('获取试卷列表失败')
    savedExams.value = []
  } finally {
    examListLoading.value = false
  }
}

// 获取知识库列表
const fetchKnowledgeBases = async () => {
  try {
    knowledgeBasesLoading.value = true
    const response = await examApi.getKnowledgeBases()
    knowledgeBases.value = response.data || response || []
  } catch (error) {
    console.error('获取知识库列表失败:', error)
    ElMessage.error('获取知识库列表失败')
    knowledgeBases.value = []
  } finally {
    knowledgeBasesLoading.value = false
  }
}

// 获取知识库文档列表
const fetchKnowledgeDocuments = async (knowledgeBaseId) => {
  if (!knowledgeBaseId) return
  
  try {
    documentsLoading.value = true
    const response = await examApi.getKnowledgeBaseDocuments(knowledgeBaseId)
    knowledgeDocuments.value = response.data?.documents || response.documents || []
  } catch (error) {
    console.error('获取知识库文档失败:', error)
    ElMessage.error('获取知识库文档失败')
    knowledgeDocuments.value = []
  } finally {
    documentsLoading.value = false
  }
}

// 知识库选择变化处理
const onKnowledgeBaseChange = async (knowledgeBaseId) => {
  selectedKnowledgeFiles.value = []
  knowledgeDocuments.value = []
  if (knowledgeBaseId) {
    await fetchKnowledgeDocuments(knowledgeBaseId)
  }
}

// 搜索文档
const searchDocuments = async () => {
  if (!selectedKnowledgeBase.value) return
  
  if (!documentSearchKeyword.value.trim()) {
    await fetchKnowledgeDocuments(selectedKnowledgeBase.value)
    return
  }
  
  try {
    documentsLoading.value = true
    const allDocs = await examApi.getKnowledgeBaseDocuments(selectedKnowledgeBase.value)
    const documents = allDocs.data?.documents || allDocs.documents || []
    
    knowledgeDocuments.value = documents.filter(doc => 
      (doc.filename || doc.original_filename || '').toLowerCase().includes(documentSearchKeyword.value.toLowerCase())
    )
  } catch (error) {
    console.error('搜索文档失败:', error)
    ElMessage.error('搜索文档失败')
  } finally {
    documentsLoading.value = false
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const fetchKnowledgeFiles = async () => {
  try {
    const response = await examApi.getKnowledgeFiles()
    knowledgeFiles.value = response.data?.items || []
  } catch (error) {
    console.error('获取知识库文件失败:', error)
    ElMessage.error('获取知识库文件失败')
    knowledgeFiles.value = []
  }
}

// 方法
const createNewExam = () => {
  selectedExam.value = null
  Object.assign(form, {
    examName: '',
    subject: '',
    difficulty: 'medium',
    duration: 90,
    totalScore: 100,
    questionTypes: ['单选题', '多选题'],
    knowledgeFiles: [],
    specialRequirements: ''
  })
  showExamEditor.value = true
}

const selectExam = (exam) => {
  selectedExam.value = exam
  showExamEditor.value = true
}

const editExam = (exam) => {
  form.examName = exam.name
  form.subject = exam.subject
  form.difficulty = exam.difficulty
  form.duration = exam.duration
  selectedExam.value = exam
  showExamEditor.value = true
}

const handleExamAction = ({ action, exam }) => {
  switch (action) {
    case 'edit':
      editExam(exam)
      break
    case 'duplicate':
      duplicateExam(exam)
      break
    case 'preview':
      previewExam(exam)
      break
    case 'delete':
      deleteExam(exam)
      break
  }
}

const duplicateExam = (exam) => {
  ElMessage.success('试卷复制成功')
}

const previewExam = (exam) => {
  ElMessage.info('预览功能开发中')
}

const deleteExam = async (exam) => {
  try {
    await ElMessageBox.confirm('确定要删除这份试卷吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const response = await examApi.deleteExam(exam.id)
    
    if (response.success) {
      ElMessage.success('试卷删除成功')
      // 刷新试卷列表
      await fetchExamList()
    } else {
      throw new Error(response.message || '删除失败')
    }
  } catch (error) {
    if (error === 'cancel') {
      // 用户取消删除
      return
    }
    console.error('删除试卷失败:', error)
    ElMessage.error('删除试卷失败，请重试')
  }
}

const generateExam = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    generating.value = true
    
    // 构建生成参数
    const generateData = {
      ...form,
      stream: true,
      conversation_id: `exam_${Date.now()}`
    }
    
    // 调用流式API
    const response = await examApi.generateExam(generateData)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') {
            generating.value = false
            ElMessage.success('试卷生成成功！')
            return
          }
          
          try {
            const parsed = JSON.parse(data)
            if (parsed.answer) {
              generatedExam.value = {
                name: form.examName,
                totalScore: form.totalScore,
                totalQuestions: 20,
                content: (generatedExam.value?.content || '') + parsed.answer
              }
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
    
  } catch (error) {
    console.error('生成试卷失败:', error)
    ElMessage.error('生成试卷失败，请重试')
    generating.value = false
  }
}

const refreshExamList = async () => {
  await fetchExamList()
  ElMessage.success('试卷列表已刷新')
}

const searchKnowledgeFiles = async (query) => {
  try {
    if (!query) {
      knowledgeFiles.value = await examApi.getKnowledgeFiles()
      return
    }
    
    const response = await examApi.searchKnowledgeFiles(query)
    knowledgeFiles.value = response.data?.items || []
  } catch (error) {
    console.error('搜索知识库文件失败:', error)
    // 降级到本地搜索
    const allFiles = await examApi.getKnowledgeFiles()
    knowledgeFiles.value = allFiles.data?.items?.filter(file =>
      file.name?.toLowerCase().includes(query.toLowerCase()) ||
      file.category?.toLowerCase().includes(query.toLowerCase()) ||
      file.tags?.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
    ) || []
  }
}

const toggleKnowledgeFile = (fileId) => {
  const index = selectedKnowledgeFiles.value.indexOf(fileId)
  if (index > -1) {
    selectedKnowledgeFiles.value.splice(index, 1)
  } else {
    selectedKnowledgeFiles.value.push(fileId)
  }
}

const confirmKnowledgeFiles = () => {
  form.knowledgeFiles = knowledgeDocuments.value.filter(doc => 
    selectedKnowledgeFiles.value.includes(doc.id)
  )
  showKnowledgeDialog.value = false
  // 重置选择状态
  selectedKnowledgeBase.value = ''
  selectedKnowledgeFiles.value = []
  knowledgeDocuments.value = []
  documentSearchKeyword.value = ''
  ElMessage.success(`已选择 ${form.knowledgeFiles.length} 个文件`)
}

const removeKnowledgeFile = (fileId) => {
  form.knowledgeFiles = form.knowledgeFiles.filter(file => file.id !== fileId)
}

const saveExam = async () => {
  if (!generatedExam.value) {
    ElMessage.error('请先生成试卷')
    return
  }
  
  try {
    const examData = {
      title: form.examName,
      description: form.description,
      subject: form.subject,
      difficulty: form.difficulty,
      duration: form.duration,
      questionTypes: form.questionTypes,
      questionCounts: form.questionCounts,
      knowledgeFiles: form.knowledgeFiles,
      content: generatedExam.value.content,
      totalQuestions: generatedExam.value.totalQuestions,
      totalScore: generatedExam.value.totalScore
    }
    
    const response = await examApi.saveExam(examData)
    
    if (response.success) {
      ElMessage.success('试卷保存成功')
      
      // 刷新试卷列表
      await fetchExamList()
      
      // 重置状态
      generatedExam.value = null
      showExamEditor.value = false
    } else {
      throw new Error(response.message || '保存失败')
    }
  } catch (error) {
    console.error('保存试卷失败:', error)
    ElMessage.error('保存试卷失败，请重试')
  }
}

const initKnowledgeFiles = async () => {
  await fetchKnowledgeBases()
  await fetchKnowledgeFiles()
}

const formatTime = (date) => {
  return new Date(date).toLocaleDateString()
}

// 初始化
onMounted(async () => {
  await refreshExamList()
  await initKnowledgeFiles()
})
</script>

<style lang="scss" scoped>
.exam-generator {
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
    max-width: 1400px;
    margin: 0 auto;
    width: 100%;
    position: relative;
    z-index: 1;
  }
}

.page-header {
  background: white;
  border-bottom: 1px solid #e5e7eb;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .header-content {
    .page-title {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 24px;
      font-weight: 600;
      color: #1f2937;
      margin: 0 0 4px 0;
      
      .el-icon {
        font-size: 24px;
        color: #3b82f6;
      }
    }
    
    .page-subtitle {
      color: #6b7280;
      margin: 0;
      font-size: 14px;
    }
  }
  
  .header-actions {
    .el-button {
      border-radius: 6px;
      font-weight: 500;
      
      &.el-button--primary {
        background: #3b82f6;
        border-color: #3b82f6;
        
        &:hover {
          background: #2563eb;
          border-color: #2563eb;
        }
      }
    }
  }
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.exam-list-panel {
  width: 320px;
  background: white;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  
  .list-header {
    padding: 16px 20px;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    align-items: center;
    justify-content: space-between;
    
    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #1f2937;
    }
    
    .el-button {
      padding: 6px 8px;
      border-radius: 4px;
      
      .el-icon {
        font-size: 14px;
      }
    }
  }
  
  .exam-list-content {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    
    &::-webkit-scrollbar {
      width: 6px;
    }
    
    &::-webkit-scrollbar-track {
      background: #f1f5f9;
    }
    
    &::-webkit-scrollbar-thumb {
      background: #cbd5e1;
      border-radius: 3px;
      
      &:hover {
        background: #94a3b8;
      }
    }
  }
}

.list-card {
  margin-bottom: 8px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: white;
  transition: all 0.2s ease;
  cursor: pointer;
  
  &:hover {
    border-color: #3b82f6;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
  }
  
  &.selected {
    border-color: #3b82f6;
    background: #eff6ff;
  }
  
  .card-content {
    padding: 12px 16px;
    
    .exam-title {
      font-size: 14px;
      font-weight: 600;
      color: #1f2937;
      margin: 0 0 8px 0;
      line-height: 1.4;
    }
    
    .exam-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 8px;
      
      .meta-item {
        font-size: 12px;
        color: #6b7280;
        display: flex;
        align-items: center;
        gap: 2px;
        
        .el-icon {
          font-size: 12px;
        }
      }
    }
    
    .exam-actions {
      display: flex;
      gap: 4px;
      
      .el-button {
        padding: 4px 8px;
        font-size: 12px;
        border-radius: 4px;
        
        &.el-button--text {
          color: #6b7280;
          
          &:hover {
            color: #3b82f6;
            background: #eff6ff;
          }
        }
      }
    }
  }
}

.editor-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f9fafb;
  
  .welcome-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px;
    text-align: center;
    
    .welcome-icon {
      font-size: 64px;
      color: #d1d5db;
      margin-bottom: 16px;
    }
    
    .welcome-title {
      font-size: 20px;
      font-weight: 600;
      color: #374151;
      margin: 0 0 8px 0;
    }
    
    .welcome-subtitle {
      font-size: 14px;
      color: #6b7280;
      margin: 0;
    }
  }
  
  .exam-editor-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: white;
    
    .editor-header {
      padding: 16px 24px;
      border-bottom: 1px solid #e5e7eb;
      display: flex;
      align-items: center;
      justify-content: space-between;
      
      .header-left {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .back-button {
          padding: 6px 8px;
          border-radius: 4px;
          
          .el-icon {
            font-size: 16px;
          }
        }
        
        .editor-title {
          font-size: 18px;
          font-weight: 600;
          color: #1f2937;
          margin: 0;
        }
      }
      
      .header-actions {
        .el-button {
          border-radius: 6px;
          font-weight: 500;
          
          &.el-button--primary {
            background: #3b82f6;
            border-color: #3b82f6;
            
            &:hover {
              background: #2563eb;
              border-color: #2563eb;
            }
          }
        }
      }
    }
    
    .editor-body {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
      
      .form-section {
        margin-bottom: 24px;
        
        .section-title {
          font-size: 16px;
          font-weight: 600;
          color: #1f2937;
          margin: 0 0 16px 0;
          display: flex;
          align-items: center;
          gap: 8px;
          
          .el-icon {
            font-size: 16px;
            color: #3b82f6;
          }
        }
      }
    }
  }
}

// 空状态样式
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
  
  .el-icon {
    font-size: 48px;
    color: #d1d5db;
    margin-bottom: 16px;
  }
  
  .empty-text {
    font-size: 14px;
    margin: 0 0 16px 0;
  }
}

// 加载状态样式
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #6b7280;
  
  .el-icon {
    margin-right: 8px;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
}

// 表单样式优化
:deep(.el-form) {
  .el-form-item {
    margin-bottom: 16px;
    
    .el-form-item__label {
      color: #374151;
      font-weight: 500;
      font-size: 14px;
      margin-bottom: 6px;
    }
  }
  
  .el-input__wrapper {
    border-radius: 6px;
    border: 1px solid #d1d5db;
    transition: all 0.2s ease;
    
    &:hover {
      border-color: #9ca3af;
    }
    
    &.is-focus {
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }
  
  .el-select {
    width: 100%;
    
    .el-input__wrapper {
      border-radius: 6px;
    }
  }
  
  .el-checkbox-group {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    
    .el-checkbox {
      margin-right: 0;
      
      .el-checkbox__label {
        font-size: 14px;
        color: #374151;
      }
    }
  }
  
  .el-input-number {
    width: 100%;
    
    .el-input__wrapper {
      border-radius: 6px;
    }
  }
}

// 知识库对话框样式
:deep(.el-dialog) {
  border-radius: 8px;
  
  .el-dialog__header {
    padding: 16px 20px;
    border-bottom: 1px solid #e5e7eb;
    
    .el-dialog__title {
      font-size: 16px;
      font-weight: 600;
      color: #1f2937;
    }
  }
  
  .el-dialog__body {
    padding: 20px;
  }
}

.knowledge-files-list {
  max-height: 300px;
  overflow-y: auto;
  
  .knowledge-file-item {
    padding: 8px 0;
    border-bottom: 1px solid #f3f4f6;
    
    &:last-child {
      border-bottom: none;
    }
  }
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 6px;
  margin-bottom: 8px;
  
  .el-icon {
    color: #6b7280;
  }
  
  span {
    flex: 1;
    font-size: 14px;
    color: #374151;
  }
}

// 动画效果
@keyframes float {
  from {
    transform: translateX(-50px);
  }
  to {
    transform: translateX(50px);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.exam-list-panel, .exam-editor-content {
  animation: fadeInUp 0.6s ease-out;
}

.exam-list-panel {
  animation-delay: 0.1s;
}

.exam-editor-content {
  animation-delay: 0.2s;
}

// 知识库选择对话框样式
.knowledge-selection-container {
  .knowledge-base-section {
    margin-bottom: 24px;
    
    h4 {
      margin: 0 0 12px 0;
      font-size: 14px;
      font-weight: 600;
      color: #303133;
    }
  }
  
  .knowledge-documents-section {
    h4 {
      margin: 0 0 12px 0;
      font-size: 14px;
      font-weight: 600;
      color: #303133;
    }
    
    .documents-search {
      margin-bottom: 16px;
    }
    
    .documents-list {
      max-height: 300px;
      overflow-y: auto;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
      padding: 8px;
      
      .empty-documents {
        text-align: center;
        padding: 40px 20px;
        color: #909399;
      }
      
      .document-item {
        padding: 8px;
        border-radius: 4px;
        transition: background-color 0.2s;
        
        &:hover {
          background-color: #f5f7fa;
        }
        
        .document-info {
          margin-left: 8px;
          
          .document-name {
            font-size: 14px;
            color: #303133;
            margin-bottom: 4px;
          }
          
          .document-meta {
            font-size: 12px;
            color: #909399;
            
            .file-size, .file-type {
              margin-right: 12px;
            }
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .exam-generator {
    .page-header {
      flex-direction: column;
      gap: 16px;
      text-align: center;
    }
    
    .main-content {
      flex-direction: column;
      height: auto;
    }
    
    .exam-list-panel {
      width: 100%;
      height: 300px;
      margin-bottom: 16px;
    }
  }
}
</style>