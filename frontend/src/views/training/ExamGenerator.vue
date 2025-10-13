<template>
  <div class="exam-generator">
    <div class="page-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><EditPen /></el-icon>
            智能试卷生成
          </h1>
          <p class="page-description">基于知识库自动生成专业考试试卷</p>
        </div>
        <div class="header-actions">
          <el-button @click="createNewExam" type="primary" size="large">
            <el-icon><Plus /></el-icon>
            新建试卷
          </el-button>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <div class="main-content">
        <!-- 左侧试卷列表 -->
        <div class="exam-list-panel">
          <el-card class="list-card">
            <template #header>
              <div class="list-header">
                
                <div class="list-actions">
                  <el-input
                    v-model="searchKeyword"
                    placeholder="搜索试卷..."
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

            <!-- 试卷列表内容 -->
            <div class="exam-list-content">
              <div v-if="examListLoading" class="loading-container">
                <el-skeleton :rows="5" animated />
              </div>
              
              <div v-else-if="examList.length === 0" class="empty-container">
                <el-empty description="暂无试卷数据" :image-size="120">
                  <el-button type="primary" @click="createNewExam">
                    <el-icon><Plus /></el-icon>
                    创建第一份试卷
                  </el-button>
                </el-empty>
              </div>

              <div v-else class="exam-items">
                <div
                  v-for="exam in examList"
                  :key="exam.id"
                  :class="['exam-item', { active: selectedExam?.id === exam.id }]"
                  @click="selectExam(exam)"
                >
                  <div class="exam-item-header">
                    <h4 class="exam-title">{{ exam.name || exam.title || '未命名试卷' }}</h4>
                    <div class="exam-actions" @click.stop>
                      <el-dropdown trigger="click">
                        <el-button text size="small">
                          <el-icon><MoreFilled /></el-icon>
                        </el-button>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item @click="shareExam(exam)">
                              <el-icon><Share /></el-icon>
                              分享
                            </el-dropdown-item>
                            <el-dropdown-item @click="deleteExam(exam)">
                              <el-icon><Delete /></el-icon>
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                  </div>
                  
                  <div class="exam-item-content">
                    <div class="exam-meta">
                      <div class="meta-item">
                        <el-icon><Clock /></el-icon>
                        <span>{{ exam.duration || 90 }}分钟</span>
                      </div>
                      <div class="meta-item">
                        <el-icon><Star /></el-icon>
                        <span>{{ exam.totalScore || 100 }}分</span>
                      </div>
                      <div class="meta-item">
                        <el-icon><Document /></el-icon>
                        <span>{{ exam.questionCount || 0 }}题</span>
                      </div>
                    </div>
                    
                    <div class="exam-status">
                      <el-tag :type="getStatusType(exam.status)" size="small">
                        {{ getStatusText(exam.status) }}
                      </el-tag>
                    </div>
                    
                    <div class="exam-time">
                      创建时间：{{ formatDate(exam.created_at) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </div>

        <!-- 中间试卷配置面板 -->
        <div class="exam-config-panel">
          <!-- 欢迎页面 -->
          <div v-if="!selectedExam && !isCreatingNew" class="welcome-container">
            <el-card class="welcome-card">
              <div class="welcome-content">
                <el-icon class="welcome-icon"><EditPen /></el-icon>
                <h2>欢迎使用智能试卷生成</h2>
                <p>选择左侧试卷进行编辑，或创建新的试卷</p>
                <div class="welcome-actions">
                  <el-button type="primary" @click="createNewExam">
                    <el-icon><Plus /></el-icon>
                    创建新试卷
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>

          <!-- 试卷配置表单 -->
          <div v-else class="config-container">
            <el-card class="config-card">
              <template #header>
                <div class="config-header">
                  <span class="config-title">
                    <el-icon><Setting /></el-icon>
                    试卷配置
                  </span>
                  <div class="config-actions">
                    <el-button @click="generateExam" type="primary" :loading="generating">
                      <el-icon><DataAnalysis /></el-icon>
                      {{ generating ? '生成中...' : 'AI生成试卷' }}
                    </el-button>
                    <el-button @click="cancelEdit" size="small">
                      <el-icon><Close /></el-icon>
                      取消
                    </el-button>
                  </div>
                </div>
              </template>

              <div class="config-content">
                <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
                  <!-- 基础信息 -->
                  <div class="form-section">
                    <h3>基础信息</h3>
                    <el-form-item label="试卷名称" prop="examName">
                      <el-input v-model="form.examName" placeholder="请输入试卷名称" />
                    </el-form-item>
                    
                    <el-form-item label="总分" prop="totalScore">
                      <el-input-number v-model="form.totalScore" :min="50" :max="200" :step="10" />
                      <span style="margin-left: 8px;">分</span>
                    </el-form-item>
                  </div>

                  <!-- 题型配置 -->
                  <div class="form-section">
                    <h3>题型配置</h3>
                    
                    <!-- 单选题 -->
                    <el-form-item label="单选题数量">
                      <el-input-number 
                        v-model="form.questionCounts.single" 
                        :min="0" 
                        :max="50" 
                        :step="1"
                        placeholder="0"
                      />
                      <span style="margin-left: 8px;">题</span>
                    </el-form-item>
                    
                    <!-- 多选题 -->
                    <el-form-item label="多选题数量">
                      <el-input-number 
                        v-model="form.questionCounts.multiple" 
                        :min="0" 
                        :max="50" 
                        :step="1"
                        placeholder="0"
                      />
                      <span style="margin-left: 8px;">题</span>
                    </el-form-item>
                    
                    <!-- 简答题 -->
                    <el-form-item label="简答题数量">
                      <el-input-number 
                        v-model="form.questionCounts.short" 
                        :min="0" 
                        :max="20" 
                        :step="1"
                        placeholder="0"
                      />
                      <span style="margin-left: 8px;">题</span>
                    </el-form-item>
                  </div>

                  <!-- 知识库选择 -->
                  <div class="form-section">
                    <h3>知识库选择</h3>
                    <el-form-item label="选择知识库" prop="knowledgeFiles">
                      <el-button @click="openKnowledgeDialog" type="primary" plain>
                        <el-icon><Folder /></el-icon>
                        选择知识库文件
                      </el-button>
                      <div v-if="form.knowledgeFiles.length > 0" class="selected-files">
                        <div class="file-list">
                          <div v-for="(file, index) in form.knowledgeFiles" :key="file.id" class="file-item">
                            <el-icon><Document /></el-icon>
                            <span>{{ file.fileName || file.filename || file.original_filename || file.name || '未命名文档' }}</span>
                            <el-button @click="removeKnowledgeFile(index)" text size="small">
                              <el-icon><Close /></el-icon>
                            </el-button>
                          </div>
                        </div>
                      </div>
                    </el-form-item>
                  </div>


                </el-form>
              </div>
            </el-card>
          </div>
        </div>

        <!-- 右侧试卷预览面板 -->
        <div class="exam-preview-panel">
          <el-card class="preview-card">
            <template #header>
              <div class="preview-header">
                <span class="preview-title">
                  <el-icon><View /></el-icon>
                  试卷预览
                </span>
                <div v-if="generatedExam" class="preview-actions">
                  <el-button @click="saveExam" size="small" type="primary">
                    <el-icon><Check /></el-icon>
                    保存试卷
                  </el-button>
                  <el-button @click="() => shareExam(selectedExam)" size="small">
                    <el-icon><Share /></el-icon>
                    分享
                  </el-button>
                </div>
              </div>
            </template>

            <div class="preview-content">
              <!-- 空状态 -->
              <div v-if="!generating && !generatedExam" class="empty-preview">
                <el-empty description="暂无内容" :image-size="100">
                  <p>配置试卷信息后，点击"AI生成试卷"按钮</p>
                </el-empty>
              </div>

              <!-- 生成中状态（无内容时） -->
              <div v-if="generating && !displayedContent" class="generating-state">
                <div class="generating-header">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <span>AI正在生成试卷...</span>
                </div>
                <el-skeleton :rows="8" animated />
              </div>

              <!-- 实时显示状态（生成中有内容时） -->
              <div v-else-if="generating && displayedContent" class="typewriter-container">
                <div class="typewriter-header">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <span>AI正在生成中...</span>
                </div>
                <div class="exam-preview">
                  <div class="preview-info">
                    <h3>{{ form.examName }}</h3>
                    <div class="preview-meta">
                      <span>总分：{{ form.totalScore }}分</span>
                      <span>正在生成中...</span>
                    </div>
                  </div>
                  <div class="preview-body">
                    <div class="content-text" v-html="formatExamContentForDisplay(displayedContent)"></div>
                  </div>
                </div>
              </div>



              <!-- 试卷预览（生成完成） -->
              <div v-else-if="generatedExam !== null" class="exam-preview">
                <div class="preview-info">
                  <h3>{{ form.examName }}</h3>
                  <div class="preview-meta">
                    <span>总分：{{ form.totalScore }}分</span>
                    <span v-if="generating">正在生成中...</span>
                    <span v-else>生成完成</span>
                  </div>
                  <div class="exam-controls">
                    <el-button 
                      type="success" 
                      @click="submitAnswers"
                      icon="Check"
                    >
                      提交答案
                    </el-button>
                  </div>
                </div>
                
                <div class="preview-body">
                  <!-- 交互式答题 -->
                  <div class="interactive-exam">
                    <!-- 答题进度指示器 -->
                    <div class="exam-progress">
                      <div class="progress-header">
                        <h4>答题进度</h4>
                        <span class="progress-text">{{ answeredCount }}/{{ parsedQuestions.length }} 题已完成</span>
                      </div>
                      <el-progress 
                        :percentage="progressPercentage" 
                        :stroke-width="8"
                        :color="progressColor"
                        class="progress-bar"
                      />
                      <div class="progress-stats">
                        <span class="stat-item">
                          <i class="el-icon-check" style="color: #67c23a;"></i>
                          已答题：{{ answeredCount }}
                        </span>
                        <span class="stat-item">
                          <i class="el-icon-warning" style="color: #e6a23c;"></i>
                          未答题：{{ parsedQuestions.length - answeredCount }}
                        </span>
                      </div>
                    </div>
                    
                    <div 
                      v-for="(question, index) in parsedQuestions" 
                      :key="question.id"
                      class="question-item"
                    >
                      <div class="question-header">
                        <span class="question-number">{{ index + 1 }}.</span>
                        <span class="question-type">{{ question.type }}</span>
                        <span class="question-score">{{ question.score }}分</span>
                      </div>
                      
                      <div class="question-content">
                        <div class="question-text">{{ question.text }}</div>
                        
                        <!-- 单选题 -->
                        <div v-if="question.type === '单选题' || question.type === '单选'" class="options-container">
                          <div 
                            v-for="option in question.options" 
                            :key="option.id"
                            class="option-item"
                          >
                            <el-radio 
                              :model-value="userAnswers[question.id]"
                              :label="option.id"
                              @change="handleSingleChoice(question.id, option.id)"
                            >
                              <span class="option-label">{{ option.id }}.</span>
                              <span class="option-text">{{ option.text }}</span>
                            </el-radio>
                          </div>
                        </div>
                        
                        <!-- 多选题 -->
                        <div v-else-if="question.type === '多选题' || question.type === '多选'" class="options-container">
                          <div 
                            v-for="option in question.options" 
                            :key="option.id"
                            class="option-item"
                          >
                            <el-checkbox 
                              :model-value="userAnswers[question.id]?.includes(option.id)"
                              @change="(checked) => handleMultipleChoice(question.id, option.id, checked)"
                            >
                              <span class="option-label">{{ option.id }}.</span>
                              <span class="option-text">{{ option.text }}</span>
                            </el-checkbox>
                          </div>
                        </div>
                        
                        <!-- 简答题 -->
                        <div v-else-if="question.type === '简答题' || question.type === '简答'" class="answer-input">
                          <el-input
                            type="textarea"
                            :model-value="userAnswers[question.id]"
                            @input="(value) => handleTextAnswer(question.id, value)"
                            placeholder="请输入您的答案..."
                            :rows="6"
                            resize="vertical"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <!-- 知识库选择对话框 -->
    <el-dialog v-model="showKnowledgeDialog" title="选择知识库文件" width="800px">
       <div class="knowledge-selection">
         <!-- 知识库选择 -->
         <div class="knowledge-base-selection">
           <el-form-item label="选择知识库">
             <el-select 
               v-model="selectedKnowledgeBase" 
               placeholder="请先选择知识库"
               @change="onKnowledgeBaseChange"
               :loading="knowledgeBasesLoading"
               style="width: 100%"
               clearable
             >
               <el-option
                 v-for="kb in knowledgeBases"
                 :key="kb.id"
                 :label="kb.name || kb.title"
                 :value="kb.id"
               />
             </el-select>
           </el-form-item>
         </div>
 
         <!-- 提示信息 -->
         <div v-if="!selectedKnowledgeBase" class="selection-hint">
           <el-alert
             title="请先选择一个知识库"
             description="选择知识库后，将显示该知识库下的所有文档供您选择"
             type="info"
             :closable="false"
             show-icon
           />
         </div>
 
         <!-- 文档搜索 -->
         <div v-if="selectedKnowledgeBase" class="document-search">
           <el-input
             v-model="documentSearchKeyword"
             placeholder="搜索文档..."
             clearable
             @input="searchKnowledgeFiles"
           >
             <template #prefix>
               <el-icon><Search /></el-icon>
             </template>
           </el-input>
         </div>
 
         <!-- 文档列表 -->
         <div v-if="selectedKnowledgeBase" class="document-list">
           <div class="document-list-header">
             <h4>文档列表</h4>
             <el-tag size="small" type="info">{{ knowledgeDocuments.length }} 个文档</el-tag>
           </div>
           
           <div v-if="documentsLoading" class="loading-container">
             <el-skeleton :rows="3" animated />
           </div>
           
           <div v-else-if="knowledgeDocuments.length === 0" class="empty-container">
             <el-empty description="该知识库暂无文档" :image-size="80" />
           </div>
           
           <div v-else class="document-items">
             <div
               v-for="doc in knowledgeDocuments"
               :key="doc.id"
               :class="['document-item', { selected: selectedKnowledgeFiles.some(f => f.id === doc.id) }]"
               @click="toggleKnowledgeFile(doc)"
             >
               <el-checkbox 
                 :model-value="selectedKnowledgeFiles.some(f => f.id === doc.id)"
                 @change="toggleKnowledgeFile(doc)"
               />
               <el-icon><Document /></el-icon>
               <span class="document-name">{{ doc.filename || doc.original_filename || '未命名文档' }}</span>
               <span class="document-size">{{ formatFileSize(doc.file_size) }}</span>
             </div>
           </div>
         </div>
 
         <!-- 已选择文件统计 -->
         <div v-if="selectedKnowledgeFiles.length > 0" class="selected-summary">
           <el-tag type="success">已选择 {{ selectedKnowledgeFiles.length }} 个文件</el-tag>
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
  EditPen, Plus, Document, Search, MoreFilled, Edit, CopyDocument, 
  Download, Delete, Clock, Star, Setting, Close, Folder, DataAnalysis,
  View, Check, Loading, FolderOpened, Refresh, Share
} from '@element-plus/icons-vue'
import { examApi } from '@/api/exam'

// 响应式数据
const formRef = ref()
const generating = ref(false)
const saving = ref(false)
const generatedExam = ref(null)
const examListLoading = ref(false)
const searchKeyword = ref('')
const showKnowledgeDialog = ref(false)

// 实时显示相关变量
const displayedContent = ref('')
const fullStreamContent = ref('')

// 试卷列表数据
const examList = ref([])
const selectedExam = ref(null)
const isCreatingNew = ref(false)

// 知识库相关数据
const knowledgeBases = ref([])
const selectedKnowledgeBase = ref('')
const knowledgeBasesLoading = ref(false)
const knowledgeDocuments = ref([])
const documentsLoading = ref(false)
const documentSearchKeyword = ref('')
const selectedKnowledgeFiles = ref([])

// 表单数据
const form = reactive({
  examName: '',
  totalScore: 100,
  questionCounts: {
    single: 10,
    multiple: 5,
    short: 2
  },
  knowledgeFiles: [],
  specialRequirements: ''
})

// 用户答案数据结构
const userAnswers = ref({})
const parsedQuestions = ref([])

// 答题进度计算
const answeredCount = computed(() => {
  return Object.keys(userAnswers.value).filter(key => {
    const answer = userAnswers.value[key]
    return answer && (Array.isArray(answer) ? answer.length > 0 : answer.trim() !== '')
  }).length
})

const progressPercentage = computed(() => {
  if (parsedQuestions.value.length === 0) return 0
  return Math.round((answeredCount.value / parsedQuestions.value.length) * 100)
})

const progressColor = computed(() => {
  const percentage = progressPercentage.value
  if (percentage < 30) return '#f56c6c'
  if (percentage < 70) return '#e6a23c'
  return '#67c23a'
})

// 表单验证规则
const rules = {
  examName: [
    { required: true, message: '请输入试卷名称', trigger: 'blur' }
  ],
  totalScore: [
    { required: true, message: '请设置总分', trigger: 'blur' },
    { type: 'number', min: 50, max: 200, message: '总分应在50-200分之间', trigger: 'blur' }
  ]
}

// 验证至少有一种题型数量大于0
const validateQuestionCounts = () => {
  const { single, multiple, short } = form.questionCounts
  if (single === 0 && multiple === 0 && short === 0) {
    ElMessage.error('请至少设置一种题型的数量大于0')
    return false
  }
  return true
}

// API调用方法
const fetchExamList = async () => {
  examListLoading.value = true
  try {
    const response = await examApi.getExamList()
    // 后端返回的数据结构是 {items: [], total: number, skip: number, limit: number}
    examList.value = response.data?.items || response.items || []
    console.log('获取到的试卷列表:', examList.value)
  } catch (error) {
    console.error('获取试卷列表失败:', error)
    ElMessage.error('获取试卷列表失败')
  } finally {
    examListLoading.value = false
  }
}

const fetchKnowledgeBases = async () => {
  knowledgeBasesLoading.value = true
  try {
    const response = await examApi.getKnowledgeBases()
    knowledgeBases.value = response || []
    console.log('知识库列表:', knowledgeBases.value)
  } catch (error) {
    console.error('获取知识库列表失败:', error)
    ElMessage.error('获取知识库列表失败')
  } finally {
    knowledgeBasesLoading.value = false
  }
}

const fetchKnowledgeDocuments = async (knowledgeBaseId) => {
  if (!knowledgeBaseId) return
  
  documentsLoading.value = true
  try {
    const response = await examApi.getKnowledgeBaseDocuments(knowledgeBaseId)
    // API返回的数据结构是 { documents: [...], total: number }
    knowledgeDocuments.value = response?.documents || []
    console.log('知识库文档:', knowledgeDocuments.value)
    console.log('文档总数:', response?.total || 0)
  } catch (error) {
    console.error('获取知识库文档失败:', error)
    ElMessage.error('获取知识库文档失败')
  } finally {
    documentsLoading.value = false
  }
}

const searchDocuments = async () => {
  if (!selectedKnowledgeBase.value) return
  
  documentsLoading.value = true
  try {
    const response = await examApi.searchKnowledgeFiles(documentSearchKeyword.value)
    // 过滤出属于当前知识库的文档
    const allDocuments = response || []
    knowledgeDocuments.value = allDocuments.filter(doc => 
      doc.knowledge_base_id === selectedKnowledgeBase.value
    )
  } catch (error) {
    console.error('搜索文档失败:', error)
    ElMessage.error('搜索文档失败')
  } finally {
    documentsLoading.value = false
  }
}

const fetchKnowledgeFiles = async () => {
  try {
    const response = await examApi.getKnowledgeFiles()
    return response || []
  } catch (error) {
    console.error('获取知识库文件失败:', error)
    ElMessage.error('获取知识库文件失败')
    return []
  }
}

// 业务逻辑方法
const createNewExam = async () => {
  selectedExam.value = null
  isCreatingNew.value = true
  // 重置表单
  Object.assign(form, {
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
  generatedExam.value = null
  
  // 加载知识库列表
  await fetchKnowledgeBases()
}

const selectExam = async (exam) => {
  try {
    selectedExam.value = exam
    isCreatingNew.value = false
    
    console.log('选择的试卷数据:', exam)
    
    // 获取试卷详情
    const response = await examApi.getExamDetail(exam.id)
    const examDetail = response.data || response
    
    console.log('获取到的试卷详情:', examDetail)
    
    // 加载试卷数据到表单，注意字段名映射
    Object.assign(form, {
      examName: examDetail.title || exam.title || exam.name || '',  // 后端返回title字段
      subject: examDetail.subject || exam.subject || '',
      difficulty: examDetail.difficulty || exam.difficulty || '',
      duration: examDetail.duration || exam.duration || 60,
      totalScore: examDetail.total_score || exam.total_score || exam.totalScore || 100,  // 后端返回total_score
      questionTypes: examDetail.question_types || exam.question_types || exam.questionTypes || ['单选题', '多选题'],  // 后端返回question_types
      questionCounts: examDetail.question_counts || exam.question_counts || exam.questionCounts || {
        single: 10,
        multiple: 5,
        judge: 5,
        fill: 3,
        short: 2,
        coding: 1
      },
      knowledgeFiles: [],  // 将在下面单独处理
      specialRequirements: examDetail.special_requirements || exam.special_requirements || exam.specialRequirements || ''  // 后端返回special_requirements
    })
    
    // 处理知识库文件数据结构
    const knowledgeFiles = examDetail.knowledge_files || exam.knowledge_files || exam.knowledgeFiles || []
    console.log('知识库文件数据:', knowledgeFiles)
    
    if (knowledgeFiles.length > 0 && typeof knowledgeFiles[0] === 'string') {
      // 旧格式：只有ID的数组，需要转换为新格式
      form.knowledgeFiles = knowledgeFiles.map(fileId => ({
        id: fileId,
        filename: '文档ID: ' + fileId.substring(0, 8) + '...',
        name: '文档ID: ' + fileId.substring(0, 8) + '...'
      }))
    } else {
      // 新格式：包含id和fileName的对象数组
      form.knowledgeFiles = knowledgeFiles.map(file => {
        const processedFile = {
          id: file.id,
          fileName: file.fileName || file.filename || '未命名文档',
          filename: file.fileName || file.filename || '未命名文档',
          name: file.fileName || file.filename || '未命名文档',
          original_filename: file.fileName || file.filename || '未命名文档'
        }
        return processedFile
      })
    }
    
    console.log('处理后的知识库文件:', form.knowledgeFiles)
    
    // 设置试卷内容
    generatedExam.value = examDetail.content || exam.content || ''
    
    // 如果有试卷内容，解析为结构化数据
    if (examDetail.content || exam.content) {
      try {
        const content = examDetail.content || exam.content
        const questions = parseExamContent(content)
        parsedQuestions.value = questions
        console.log('选择试卷解析的题目数量:', questions.length)
      } catch (error) {
        console.error('解析试卷内容失败:', error)
        parsedQuestions.value = []
      }
    } else {
      parsedQuestions.value = []
    }
    
    console.log('表单数据已更新:', form)
    ElMessage.success('试卷数据已加载')
    
  } catch (error) {
    console.error('获取试卷详情失败:', error)
    ElMessage.error('获取试卷详情失败')
    
    // 如果获取详情失败，使用列表中的基本信息
    selectedExam.value = exam
    isCreatingNew.value = false
    
    Object.assign(form, {
      examName: exam.title || exam.name || '',
      subject: exam.subject || '',
      difficulty: exam.difficulty || '',
      duration: exam.duration || 60,
      totalScore: exam.total_score || exam.totalScore || 100,
      questionTypes: exam.question_types || exam.questionTypes || ['单选题', '多选题'],
      questionCounts: exam.question_counts || exam.questionCounts || {
        single: 10,
        multiple: 5,
        judge: 5,
        fill: 3,
        short: 2,
        coding: 1
      },
      knowledgeFiles: exam.knowledge_files || exam.knowledgeFiles || [],
      specialRequirements: exam.special_requirements || exam.specialRequirements || ''
    })
    
    generatedExam.value = exam.content || ''
    parsedQuestions.value = []
  }
}

const editExam = (exam) => {
  selectExam(exam)
}

const copyExam = async (exam) => {
  try {
    const response = await examApi.duplicateExam(exam.id)
    ElMessage.success('试卷复制成功')
    await fetchExamList()
  } catch (error) {
    console.error('复制试卷失败:', error)
    ElMessage.error('复制试卷失败')
  }
}

const previewExam = (exam) => {
  selectExam(exam)
}

const deleteExam = async (exam) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除试卷"${exam.name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await examApi.deleteExam(exam.id)
    ElMessage.success('试卷删除成功')
    await fetchExamList()
    
    // 如果删除的是当前选中的试卷，清空选择
    if (selectedExam.value?.id === exam.id) {
      selectedExam.value = null
      generatedExam.value = null
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除试卷失败:', error)
      ElMessage.error('删除试卷失败')
    }
  }
}

const loadExam = async (exam) => {
  try {
    // 获取试卷详情
    const response = await examApi.getExamDetail(exam.id)
    const examDetail = response.data
    
    // 重置表单数据
    form.examName = examDetail.title || examDetail.exam_name || ''
    form.totalScore = examDetail.total_score || 100
    form.questionCounts = examDetail.question_counts || {
      single: 10,
      multiple: 5,
      short: 2
    }
    // 处理知识库文件数据结构
    const knowledgeFiles = examDetail.knowledge_files || []
    console.log('知识库文件数据:', knowledgeFiles)
    
    if (knowledgeFiles.length > 0 && typeof knowledgeFiles[0] === 'string') {
      // 旧格式：只有ID的数组，需要转换为新格式
      form.knowledgeFiles = knowledgeFiles.map(fileId => ({
        id: fileId,
        filename: '文档ID: ' + fileId.substring(0, 8) + '...',
        name: '文档ID: ' + fileId.substring(0, 8) + '...'
      }))
    } else {
      // 新格式：包含id和fileName的对象数组
      form.knowledgeFiles = knowledgeFiles.map(file => {
        const processedFile = {
          id: file.id,
          fileName: file.fileName || file.filename || '未命名文档',
          filename: file.fileName || file.filename || '未命名文档',
          name: file.fileName || file.filename || '未命名文档',
          original_filename: file.fileName || file.filename || '未命名文档'
        }
        return processedFile
      })
    }
    
    console.log('处理后的知识库文件:', form.knowledgeFiles)
    form.specialRequirements = examDetail.special_requirements || ''
    
    // 设置生成的试卷内容
    generatedExam.value = examDetail.content
    
    // 解析试题数据
    if (examDetail.questions && examDetail.questions.length > 0) {
      parsedQuestions.value = examDetail.questions.map(q => ({
        id: q.id || `q_${q.number}`,
        number: q.number,
        type: q.type,
        text: q.text,
        options: q.options || [],
        correct_answers: q.correct_answers,
        score: q.score,
        explanation: q.explanation || ''
      }))
      console.log('解析的试题数据:', parsedQuestions.value)
    } else {
      parsedQuestions.value = []
    }
    
    // 设置选中的试卷
    selectedExam.value = exam
    
    ElMessage.success('试卷加载成功')
  } catch (error) {
    console.error('加载试卷失败:', error)
    ElMessage.error('加载试卷失败')
  }
}

const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}



const generateExam = async () => {
  if (!formRef.value) return
  
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  // 验证题型数量
  if (!validateQuestionCounts()) {
    return
  }
  
  if (form.knowledgeFiles.length === 0) {
    ElMessage.warning('请选择知识库文件')
    return
  }
  
  generating.value = true
  // 重置所有相关状态
  generatedExam.value = null
  displayedContent.value = ''
  fullStreamContent.value = ''
  
  try {
    // 构建题型列表
    const questionTypes = []
    const questionCounts = {}
    
    if (form.questionCounts.single > 0) {
      questionTypes.push('单选题')
      questionCounts.single_choice = form.questionCounts.single
    }
    if (form.questionCounts.multiple > 0) {
      questionTypes.push('多选题')
      questionCounts.multiple_choice = form.questionCounts.multiple
    }
    if (form.questionCounts.short > 0) {
      questionTypes.push('简答题')
      questionCounts.short_answer = form.questionCounts.short
    }
    
    const requestData = {
      title: form.examName,
      subject: form.examName, // 使用试卷名称作为科目
      total_score: form.totalScore,
      question_types: questionTypes,
      question_counts: questionCounts,
      knowledge_files: form.knowledgeFiles.map(file => file.id),
      special_requirements: form.specialRequirements,
      stream: true
    }
    
    // 使用流式API生成试卷，实现实时显示
    const response = await examApi.generateExam(requestData, (chunk, fullContent) => {
      // 累积完整内容
      fullStreamContent.value = fullContent
      // 实时显示内容（参考JD生成的实现）
      displayedContent.value = fullContent
    })
    
    // 流式传输完成，直接设置最终内容
    if (fullStreamContent.value) {
      console.log('试卷生成完成，设置最终内容')
      generatedExam.value = fullStreamContent.value
      
      // 解析试卷内容为结构化数据
      const questions = parseExamContent(fullStreamContent.value)
      parsedQuestions.value = questions
      console.log('解析的题目数量:', questions.length)
      
      // 清理临时状态
      displayedContent.value = ''
      fullStreamContent.value = ''
      ElMessage.success('试卷生成成功')
    } else {
      console.log('没有接收到试卷内容')
      ElMessage.warning('未收到试卷内容，请重试')
    }
  } catch (error) {
    console.error('生成试卷失败:', error)
    ElMessage.error('生成试卷失败，请重试')
  } finally {
    generating.value = false
  }
}

// 测试试卷格式化功能


const refreshExamList = async () => {
  await fetchExamList()
}

const searchKnowledgeFiles = async () => {
  if (!documentSearchKeyword.value.trim()) {
    await fetchKnowledgeDocuments(selectedKnowledgeBase.value)
    return
  }
  await searchDocuments()
}

const toggleKnowledgeFile = (file) => {
  const index = selectedKnowledgeFiles.value.findIndex(f => f.id === file.id)
  if (index > -1) {
    selectedKnowledgeFiles.value.splice(index, 1)
  } else {
    selectedKnowledgeFiles.value.push(file)
  }
}

const confirmKnowledgeFiles = () => {
  form.knowledgeFiles = [...selectedKnowledgeFiles.value]
  showKnowledgeDialog.value = false
  ElMessage.success(`已选择 ${form.knowledgeFiles.length} 个文件`)
}

const removeKnowledgeFile = (index) => {
  form.knowledgeFiles.splice(index, 1)
}

const saveExam = async () => {
  if (!generatedExam.value) {
    ElMessage.warning('请先生成试卷')
    return
  }
  
  saving.value = true
  try {
    const examData = {
      id: selectedExam.value?.id || generateUUID(),
      title: form.examName,
      subject: form.subject,
      difficulty: form.difficulty,
      duration: form.duration,
      total_score: form.totalScore,
      question_types: form.questionTypes,
      question_counts: form.questionCounts,
      knowledge_files: form.knowledgeFiles.map(file => ({
        id: file.id,
        fileName: file.filename || file.original_filename || file.name || '未命名文档'
      })),
      special_requirements: form.specialRequirements,
      content: generatedExam.value,
      questions: parsedQuestions.value,  // 添加结构化试题数据
      createdAt: selectedExam.value?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
    
    if (selectedExam.value?.id) {
      const updatedExam = await examApi.updateExam(selectedExam.value.id, examData)
      ElMessage.success('试卷更新成功')
      // 更新selectedExam数据
      selectedExam.value = { ...selectedExam.value, ...examData }
    } else {
      const savedExam = await examApi.saveExam(examData)
      console.log('savedExam response:', savedExam)
      ElMessage.success('试卷保存成功')
      // 设置selectedExam为后端返回的试卷数据（包含正确的ID）
      selectedExam.value = savedExam.data || savedExam
      console.log('selectedExam.value after save:', selectedExam.value)
    }
    
    await fetchExamList()
  } catch (error) {
    console.error('保存试卷失败:', error)
    ElMessage.error('保存试卷失败，请重试')
  } finally {
    saving.value = false
  }
}

const openKnowledgeDialog = async () => {
  showKnowledgeDialog.value = true
  selectedKnowledgeFiles.value = [...form.knowledgeFiles]
  
  // 重置选择状态
  selectedKnowledgeBase.value = ''
  documentSearchKeyword.value = ''
  knowledgeDocuments.value = []
  
  // 加载知识库列表
  await fetchKnowledgeBases()
}

// 监听知识库选择变化
const onKnowledgeBaseChange = async (knowledgeBaseId) => {
  selectedKnowledgeBase.value = knowledgeBaseId
  documentSearchKeyword.value = ''
  knowledgeDocuments.value = []
  
  if (knowledgeBaseId) {
    await fetchKnowledgeDocuments(knowledgeBaseId)
  }
}

// 格式化文件大小
const formatFileSize = (size) => {
  if (!size || size === 0) return '未知大小'
  
  const units = ['B', 'KB', 'MB', 'GB']
  let unitIndex = 0
  let fileSize = size
  
  while (fileSize >= 1024 && unitIndex < units.length - 1) {
    fileSize /= 1024
    unitIndex++
  }
  
  return `${fileSize.toFixed(1)} ${units[unitIndex]}`
}

const cancelEdit = () => {
  isCreatingNew.value = false
  selectedExam.value = null
  resetForm()
}

const resetForm = () => {
  Object.assign(form, {
    examName: '',
    subject: '',
    difficulty: 'medium',
    duration: 90,
    totalScore: 100,
    questionTypes: ['单选题', '多选题'],
    knowledgeFiles: []
  })
  generatedExam.value = null
}

const shareExam = async (exam) => {
  // 实现试卷分享功能
  let examData = exam
  
  console.log('shareExam called with:', exam)
  console.log('selectedExam.value:', selectedExam.value)
  
  // 如果没有传入具体的试卷对象，检查当前选中的试卷
  if (!examData) {
    if (selectedExam.value && selectedExam.value.id) {
      examData = selectedExam.value
    } else if (generatedExam.value) {
      // 如果有生成的试卷但没有保存，提示用户先保存
      ElMessageBox.confirm(
        '需要先保存试卷才能分享。是否现在保存试卷？',
        '提示',
        {
          confirmButtonText: '保存并分享',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        await saveExam()
        // 保存成功后，使用选中的试卷进行分享
        if (selectedExam.value && selectedExam.value.id) {
          await shareExam(selectedExam.value)
        }
      }).catch(() => {
        // 用户取消
      })
      return
    } else {
      ElMessage.warning('没有可分享的试卷')
      return
    }
  }
  
  // 检查试卷是否有ID
  console.log('examData before ID check:', examData)
  console.log('examData.id:', examData.id)
  if (!examData.id) {
    ElMessage.warning('试卷ID不存在，无法生成分享链接')
    return
  }
  
  try {
    // 生成分享链接
    const shareUrl = `${window.location.origin}/exam-share/${examData.id}`
    
    // 复制到剪贴板
    await navigator.clipboard.writeText(shareUrl)
    
    // 显示分享链接对话框
    ElMessageBox.alert(
      `分享链接已复制到剪贴板：<br/><br/><code style="background: #f5f5f5; padding: 8px; border-radius: 4px; word-break: break-all;">${shareUrl}</code>`,
      '试卷分享',
      {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '确定',
        type: 'success'
      }
    )
    
    ElMessage.success('分享链接已复制到剪贴板')
  } catch (error) {
    console.error('分享失败:', error)
    ElMessage.error('分享失败，请重试')
  }
}

const handleExamAction = ({ action, exam }) => {
  switch (action) {
    case 'edit':
      selectExam(exam)
      break
    case 'duplicate':
      ElMessage.success('试卷复制成功！')
      break
    case 'download':
      ElMessage.success('试卷下载成功！')
      break
    case 'delete':
      ElMessageBox.confirm('确定要删除这份试卷吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        ElMessage.success('试卷删除成功！')
      })
      break
  }
}

const handleSearch = () => {
  // 搜索逻辑
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    // 如果搜索关键词为空，重新加载所有试卷
    fetchExamList()
    return
  }
  
  // 过滤试卷列表
  const filteredExams = examList.value.filter(exam => 
    (exam.name || exam.title || '').toLowerCase().includes(keyword.toLowerCase()) ||
    (exam.subject || '').toLowerCase().includes(keyword.toLowerCase())
  )
  
  // 这里可以实现服务端搜索
  ElMessage.info(`找到 ${filteredExams.length} 个相关试卷`)
}

// 解析试卷内容为结构化数据
const parseExamContent = (content) => {
  if (!content || typeof content !== 'string') return []
  
  console.log('开始解析试卷内容:', content)
  
  const questions = content.split('***').filter(q => q.trim())
  const parsedQuestions = []
  
  questions.forEach((questionData, index) => {
    const parts = questionData.trim().split('|')
    console.log(`题目 ${index + 1} 分割结果:`, parts)
    
    if (parts.length !== 6) {
      console.warn(`题目 ${index + 1} 格式不正确，分割后长度为 ${parts.length}，期望为 6`)
      return
    }
    
    const [questionText, questionType, options, correctAnswers, score, explanation] = parts
    const questionId = `q_${index + 1}`
    
    console.log(`题目 ${index + 1} 解析信息:`, {
      questionText,
      questionType,
      options,
      correctAnswers,
      score,
      explanation
    })
    
    const question = {
      id: questionId,
      number: index + 1,
      text: questionText,
      type: questionType,
      score: parseInt(score) || 0,
      correct_answers: correctAnswers,
      explanation: explanation,
      options: []
    }
    
    if (questionType === '单选题' || questionType === '多选题' || questionType === '单选' || questionType === '多选') {
      if (options && options.trim()) {
        question.options = options.split(';').filter(opt => opt.trim()).map((option, optIndex) => ({
          id: String.fromCharCode(65 + optIndex),
          text: option.trim()
        }))
        console.log(`题目 ${index + 1} 解析后的选项:`, question.options)
      } else {
        console.warn(`题目 ${index + 1} 是${questionType}但没有选项数据`)
      }
    }
    
    parsedQuestions.push(question)
  })
  
  console.log('最终解析结果:', parsedQuestions)
  return parsedQuestions
}

// 格式化试卷内容为交互式组件
const formatExamContent = (content) => {
  if (!content) return ''
  
  // 解析试卷内容
  const questions = parseExamContent(content)
  parsedQuestions.value = questions
  
  // 初始化用户答案
  initializeUserAnswers(questions)
  
  // 返回空字符串，因为我们将使用Vue组件渲染
  return ''
}



// 初始化用户答案数据结构
const initializeUserAnswers = (questions) => {
  const answers = {}
  questions.forEach(question => {
    if (question.type === '单选题' || question.type === '单选') {
      answers[question.id] = ''
    } else if (question.type === '多选题' || question.type === '多选') {
      answers[question.id] = []
    } else if (question.type === '简答题' || question.type === '简答') {
      answers[question.id] = ''
    }
  })
  userAnswers.value = answers
}

// 处理单选题选择
const handleSingleChoice = (questionId, optionId) => {
  userAnswers.value[questionId] = optionId
}

// 处理多选题选择
const handleMultipleChoice = (questionId, optionId, checked) => {
  if (!userAnswers.value[questionId]) {
    userAnswers.value[questionId] = []
  }
  
  if (checked) {
    if (!userAnswers.value[questionId].includes(optionId)) {
      userAnswers.value[questionId].push(optionId)
    }
  } else {
    const index = userAnswers.value[questionId].indexOf(optionId)
    if (index > -1) {
      userAnswers.value[questionId].splice(index, 1)
    }
  }
}

// 处理简答题输入
const handleTextAnswer = (questionId, value) => {
  userAnswers.value[questionId] = value
}



// 提交答案到后端
const submitAnswers = async () => {
  try {
    // 验证答案完整性
    const unansweredQuestions = []
    parsedQuestions.value.forEach((question, index) => {
      const answer = userAnswers.value[question.id]
      if (!answer || (Array.isArray(answer) && answer.length === 0) || answer.trim?.() === '') {
        unansweredQuestions.push(index + 1)
      }
    })
    
    if (unansweredQuestions.length > 0) {
      ElMessageBox.confirm(
        `您还有 ${unansweredQuestions.length} 道题目未作答（第 ${unansweredQuestions.join('、')} 题），确定要提交吗？`,
        '提交确认',
        {
          confirmButtonText: '确定提交',
          cancelButtonText: '继续答题',
          type: 'warning',
        }
      ).then(() => {
        doSubmitAnswers()
      }).catch(() => {
        ElMessage.info('请继续完成答题')
      })
    } else {
      ElMessageBox.confirm(
        '确定要提交答案吗？提交后将无法修改。',
        '提交确认',
        {
          confirmButtonText: '确定提交',
          cancelButtonText: '再检查一下',
          type: 'info',
        }
      ).then(() => {
        doSubmitAnswers()
      })
    }
  } catch (error) {
    console.error('提交答案失败：', error)
    ElMessage.error('提交答案失败，请重试')
  }
}

// 执行答案提交
const doSubmitAnswers = async () => {
  const loading = ElLoading.service({
    lock: true,
    text: '正在提交答案...',
    background: 'rgba(0, 0, 0, 0.7)'
  })
  
  try {
    const examData = {
      examId: selectedExam.value?.id || 'test_exam',
      examName: form.examName || '测试试卷',
      answers: userAnswers.value,
      questions: parsedQuestions.value,
      submitTime: new Date().toISOString(),
      totalQuestions: parsedQuestions.value.length,
      answeredQuestions: Object.keys(userAnswers.value).filter(key => {
        const answer = userAnswers.value[key]
        return answer && (Array.isArray(answer) ? answer.length > 0 : answer.trim() !== '')
      }).length
    }
    
    console.log('提交答案数据：', examData)
    
    // 模拟提交延迟
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    ElMessage.success({
      message: '答案提交成功！系统正在阅卷中...',
      duration: 3000
    })
    
    // 这里可以调用后端API进行阅卷
    // const result = await examApi.submitAnswers(examData)
    
    // 提交成功后可以显示结果或跳转到结果页面
    showSubmissionResult(examData)
    
  } catch (error) {
    console.error('提交答案失败：', error)
    ElMessage.error('提交答案失败，请重试')
  } finally {
    loading.close()
  }
}

// 显示提交结果
const showSubmissionResult = (examData) => {
  ElMessageBox.alert(
    `<div style="text-align: left;">
      <p><strong>试卷名称：</strong>${examData.examName}</p>
      <p><strong>总题数：</strong>${examData.totalQuestions} 题</p>
      <p><strong>已答题数：</strong>${examData.answeredQuestions} 题</p>
      <p><strong>提交时间：</strong>${new Date(examData.submitTime).toLocaleString()}</p>
      <p style="color: #67c23a; margin-top: 16px;"><strong>✓ 答案已成功提交，请等待阅卷结果</strong></p>
    </div>`,
    '提交成功',
    {
      confirmButtonText: '确定',
      dangerouslyUseHTMLString: true,
      type: 'success'
    }
  )
}

// 获取题型对应的CSS类名
const getQuestionTypeClass = (questionType) => {
  const typeMap = {
    '单选题': 'single-choice',
    '多选题': 'multiple-choice',
    '简答题': 'short-answer'
  }
  return typeMap[questionType] || 'default'
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getStatusType = (status) => {
  const statusMap = {
    'draft': 'info',
    'published': 'success',
    'archived': 'warning'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    'draft': '草稿',
    'published': '已发布',
    'archived': '已归档'
  }
  return statusMap[status] || '草稿'
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

// 生命周期
onMounted(async () => {
  await fetchExamList()
})
</script>

<style lang="scss" scoped>
.exam-generator {
  min-height: 100vh;
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
    z-index: 1;
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
        color: #606266;
        font-size: 16px;
      }
    }

    .header-actions {
      .el-button {
        border-radius: 8px;
        font-weight: 500;
        padding: 12px 24px;
      }
    }
  }

  .main-content {
    display: grid;
    grid-template-columns: 280px 1fr 500px;
    gap: 20px;
    flex: 1;
    min-height: 0;
  }

  // 试卷列表面板
  .exam-list-panel {
    .list-card {
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      height: calc(100vh - 200px);
      
      :deep(.el-card__header) {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border-radius: 16px 16px 0 0;
        
        .list-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          
          .list-title {
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
          }
        }
      }
      
      :deep(.el-card__body) {
        padding: 0;
        height: calc(100% - 60px);
        overflow: hidden;
      }
    }

    .exam-list-content {
      height: 100%;
      display: flex;
      flex-direction: column;

      .loading-container,
      .empty-container {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
      }

      .exam-items {
        flex: 1;
        overflow-y: auto;
        padding: 16px;

        .exam-item {
          padding: 16px;
          margin-bottom: 12px;
          border-radius: 12px;
          background: rgba(255, 255, 255, 0.8);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.3);
          cursor: pointer;
          transition: all 0.3s;

          &:hover {
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
            transform: translateY(-2px);
          }

          &.active {
            background: rgba(102, 126, 234, 0.1);
            border-color: #667eea;
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
          }

          .exam-item-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;

            .exam-title {
              margin: 0;
              font-size: 16px;
              font-weight: 600;
              color: #303133;
              flex: 1;
            }
          }

          .exam-item-content {
            .exam-meta {
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

            .exam-status {
              margin-bottom: 8px;
            }

            .exam-time {
              font-size: 12px;
              color: #909399;
            }
          }
        }
      }
    }
  }

  // 配置面板
  .exam-config-panel {
    .welcome-container {
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;

      .welcome-card {
        width: 100%;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);

        .welcome-content {
          text-align: center;
          padding: 40px 20px;

          .welcome-icon {
            font-size: 64px;
            color: #667eea;
            margin-bottom: 24px;
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
        }
      }
    }

    .config-container {
      height: calc(100vh - 200px);

      .config-card {
        height: 100%;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);

        :deep(.el-card__header) {
          background: linear-gradient(45deg, #667eea, #764ba2);
          color: white;
          border-radius: 16px 16px 0 0;

          .config-header {
            display: flex;
            justify-content: space-between;
            align-items: center;

            .config-title {
              font-weight: 600;
              display: flex;
              align-items: center;
              gap: 8px;
            }
          }
        }

        :deep(.el-card__body) {
          height: calc(100% - 60px);
          overflow-y: auto;
        }
      }

      .config-content {
        .form-section {
          margin-bottom: 32px;
          padding-bottom: 24px;
          border-bottom: 1px solid #ebeef5;

          &:last-child {
            border-bottom: none;
          }

          h3 {
            margin: 0 0 16px 0;
            color: #303133;
            font-size: 18px;
            font-weight: 600;
          }
        }

        .selected-files {
          margin-top: 12px;

          .file-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;

            .file-item {
              display: flex;
              align-items: center;
              gap: 8px;
              padding: 8px 12px;
              background: #f5f7fa;
              border-radius: 6px;
              font-size: 14px;
            }
          }
        }

        .form-actions {
          text-align: center;
          padding-top: 24px;

          .el-button {
            padding: 12px 32px;
            font-size: 16px;
            border-radius: 8px;
          }
        }
      }
    }
  }

  // 预览面板
  .exam-preview-panel {
    .preview-card {
      height: calc(100vh - 200px);
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);

      :deep(.el-card__header) {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border-radius: 16px 16px 0 0;

        .preview-header {
          display: flex;
          justify-content: space-between;
          align-items: center;

          .preview-title {
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
          }

          .preview-actions {
            display: flex;
            gap: 8px;
          }
        }
      }

      :deep(.el-card__body) {
        height: calc(100% - 60px);
        overflow-y: auto;
      }
    }

    .preview-content {
      height: 100%;

      .empty-preview {
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
      }

      .generating-preview {
        .generating-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 20px;
          font-size: 16px;
          color: #667eea;
        }
      }

      .exam-preview {
        .preview-info {
          margin-bottom: 24px;
          padding-bottom: 16px;
          border-bottom: 1px solid #ebeef5;

          h3 {
            margin: 0 0 12px 0;
            color: #303133;
            font-size: 20px;
          }

          .preview-meta {
            display: flex;
            gap: 16px;
            font-size: 14px;
            color: #606266;
          }
        }

        .preview-body {
        }
      }
    }
  }
}

@keyframes float {
  0% {
    transform: translate(-50%, -50%) rotate(0deg);
  }
  100% {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}

// 知识库对话框样式
.knowledge-selection {
  .knowledge-base-selection {
    margin-bottom: 20px;
  }

  .document-search {
    margin-bottom: 16px;
  }

  .document-list {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #dcdfe6;
    border-radius: 8px;
    padding: 8px;

    .loading-container,
    .empty-container {
      padding: 40px 20px;
      text-align: center;
    }

    .document-items {
      .document-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid transparent;

        &:hover {
          background-color: #f5f7fa;
        }

        &.selected {
          background-color: #ecf5ff;
          border-color: #409eff;
        }

        .document-name {
          flex: 1;
          font-size: 14px;
          color: #303133;
        }

        .document-size {
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }

  .selected-summary {
    margin-top: 16px;
    text-align: center;
  }
}

// 打字机效果样式
.typewriter-container {
  .typewriter-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    color: #409eff;
    font-weight: 500;
    
    .el-icon {
      font-size: 16px;
    }
  }
  
}

// 生成状态样式
.generating-state {
  .generating-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    color: #409eff;
    font-weight: 500;
    
    .el-icon {
      font-size: 16px;
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .exam-generator {
    .main-content {
      grid-template-columns: 300px 1fr 350px;
    }
  }
}

@media (max-width: 768px) {
  .exam-generator {
    .page-header {
      flex-direction: column;
      gap: 16px;
      text-align: center;
    }
    
    .main-content {
      grid-template-columns: 1fr;
      grid-template-rows: auto auto auto;
    }
  }
}

// 交互式试卷样式 - 全新现代化设计
.exam-controls {
  display: flex;
  gap: 16px;
  margin-top: 24px;
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.interactive-exam {
  background: #f8fafc;
  border-radius: 20px;
  padding: 24px;
  margin-top: 20px;
  
  .exam-progress {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 32px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
    
    .progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      
      h4 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: #1e293b;
      }
      
      .progress-text {
        font-size: 14px;
        color: #64748b;
        font-weight: 500;
      }
    }
    
    .progress-bar {
      margin-bottom: 16px;
      
      :deep(.el-progress-bar__outer) {
        border-radius: 8px;
        background: #f1f5f9;
      }
      
      :deep(.el-progress-bar__inner) {
        border-radius: 8px;
        transition: all 0.3s ease;
      }
    }
    
    .progress-stats {
      display: flex;
      gap: 24px;
      
      .stat-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 500;
        color: #475569;
        
        i {
          font-size: 16px;
        }
      }
    }
  }
  
  .question-item {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 36px;
    margin-bottom: 28px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
      opacity: 0;
      transition: opacity 0.3s ease;
    }
    
    &:hover {
      transform: translateY(-4px);
      border-color: #c7d2fe;
      box-shadow: 0 16px 48px rgba(102, 126, 234, 0.15);
      
      &::before {
        opacity: 1;
      }
    }
    
    .question-header {
      display: flex;
      align-items: center;
      gap: 20px;
      margin-bottom: 28px;
      padding-bottom: 20px;
      border-bottom: 2px solid #f1f5f9;
      
      .question-number {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 20px;
        font-weight: 700;
        border-radius: 50%;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
      }
      
      .question-type {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
      }
      
      .question-score {
        background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
        color: white;
        padding: 10px 16px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(6, 182, 212, 0.3);
      }
    }
    
    .question-content {
      .question-text {
        font-size: 16px;
        line-height: 1.6;
        color: #1e293b;
        margin-bottom: 20px;
        font-weight: 500;
        letter-spacing: 0.2px;
      }
      
      .options-container {
        display: grid;
        gap: 12px;
        
        .option-item {
          background: #f8fafc;
          border: 2px solid #e2e8f0;
          border-radius: 12px;
          padding: 16px;
          transition: all 0.3s ease;
          cursor: pointer;
          
          &:hover {
            background: #f1f5f9;
            border-color: #c7d2fe;
            transform: translateX(4px);
          }
          
          :deep(.el-radio) {
            width: 100%;
            margin: 0;
            
            .el-radio__input {
              margin-right: 16px;
              
              .el-radio__inner {
                width: 24px;
                height: 24px;
                border: 3px solid #d1d5db;
                background: #ffffff;
                
                &::after {
                  width: 10px;
                  height: 10px;
                  background: #667eea;
                  border-radius: 50%;
                }
              }
              
              &.is-checked .el-radio__inner {
                border-color: #667eea;
                background: #ffffff;
              }
            }
            
            .el-radio__label {
              font-size: 14px;
              line-height: 1.5;
              color: #374151;
              font-weight: 500;
              word-wrap: break-word;
              word-break: break-all;
              white-space: normal;
              display: flex;
              align-items: flex-start;
              
              .option-label {
                font-weight: 700;
                color: #667eea;
                margin-right: 8px;
                flex-shrink: 0;
              }
              
              .option-text {
                flex: 1;
                word-wrap: break-word;
                word-break: break-all;
                white-space: normal;
              }
            }
          }
          
          :deep(.el-checkbox) {
            width: 100%;
            margin: 0;
            
            .el-checkbox__input {
              margin-right: 16px;
              
              .el-checkbox__inner {
                width: 24px;
                height: 24px;
                border: 3px solid #d1d5db;
                background: #ffffff;
                border-radius: 6px;
                
                &::after {
                  width: 8px;
                  height: 12px;
                  border: 3px solid #ffffff;
                  border-left: 0;
                  border-top: 0;
                  left: 7px;
                  top: 3px;
                }
              }
              
              &.is-checked .el-checkbox__inner {
                border-color: #667eea;
                background: #667eea;
              }
            }
            
            .el-checkbox__label {
              font-size: 14px;
              line-height: 1.5;
              color: #374151;
              font-weight: 500;
              word-wrap: break-word;
              word-break: break-all;
              white-space: normal;
              display: flex;
              align-items: flex-start;
              
              .option-label {
                font-weight: 700;
                color: #667eea;
                margin-right: 8px;
                flex-shrink: 0;
              }
              
              .option-text {
                flex: 1;
                word-wrap: break-word;
                word-break: break-all;
                white-space: normal;
              }
            }
          }
        }
      }
      
      .answer-input {
        :deep(.el-textarea) {
          .el-textarea__inner {
            font-size: 14px;
            line-height: 1.6;
            padding: 20px;
            border: 3px solid #e2e8f0;
            border-radius: 16px;
            background: #ffffff;
            transition: all 0.3s ease;
            min-height: 120px;
            resize: vertical;
            
            &:focus {
              border-color: #667eea;
              background: #ffffff;
              box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
              outline: none;
            }
            
            &::placeholder {
              color: #94a3b8;
              font-style: italic;
              font-size: 16px;
            }
          }
        }
      }
    }
  }
}
</style>