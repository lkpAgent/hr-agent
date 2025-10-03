<template>
  <div class="exam-generator">
    <div class="page-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-content">
          <h1 class="page-title">
            <el-icon><EditPen /></el-icon>
            智能试卷生成
          </h1>
          <p class="page-subtitle">
            基于知识库自动生成专业考试试卷
          </p>
        </div>
        <div class="header-actions">
          <el-button @click="resetForm">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </div>
      </div>

      <!-- 试卷列表区域 -->
      <div class="exam-list-section">
        <el-card class="exam-list-card">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon><Files /></el-icon>
                <span>已生成试卷</span>
                <el-tag type="info" size="small">{{ savedExams.length }}</el-tag>
              </div>
              <div class="header-actions">
                <el-button size="small" @click="refreshExamList">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
          </template>

          <div class="exam-list-content">
            <div v-if="savedExams.length === 0" class="empty-exam-list">
              <el-empty description="暂无已生成的试卷" :image-size="80">
                <el-button type="primary" @click="scrollToConfig">
                  <el-icon><Plus /></el-icon>
                  创建第一份试卷
                </el-button>
              </el-empty>
            </div>
            
            <div v-else class="exam-grid">
              <div 
                v-for="exam in savedExams" 
                :key="exam.id"
                class="exam-item"
                @click="selectExam(exam)"
                :class="{ active: selectedExam?.id === exam.id }"
              >
                <div class="exam-header">
                  <h4 class="exam-title">{{ exam.name }}</h4>
                  <el-tag :type="getDifficultyType(exam.difficulty)" size="small">
                    {{ exam.difficulty }}
                  </el-tag>
                </div>
                
                <div class="exam-info">
                  <div class="info-item">
                    <el-icon><Clock /></el-icon>
                    <span>{{ exam.duration }}分钟</span>
                  </div>
                  <div class="info-item">
                    <el-icon><Document /></el-icon>
                    <span>{{ exam.totalQuestions }}题</span>
                  </div>
                  <div class="info-item">
                    <el-icon><Star /></el-icon>
                    <span>{{ exam.totalScore }}分</span>
                  </div>
                </div>
                
                <div class="exam-meta">
                  <span class="domain">{{ exam.domain }}</span>
                  <span class="created-time">{{ formatTime(exam.createdAt) }}</span>
                </div>
                
                <div class="exam-actions" @click.stop>
                  <el-button size="small" type="primary" @click="previewExam(exam)">
                    <el-icon><View /></el-icon>
                    预览
                  </el-button>
                  <el-button size="small" @click="editExam(exam)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-button>
                  <el-button size="small" @click="duplicateExam(exam)">
                    <el-icon><CopyDocument /></el-icon>
                    复制
                  </el-button>
                  <el-button size="small" type="danger" @click="deleteExam(exam)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <div class="content-grid">
        <!-- 左侧配置面板 -->
        <div class="config-panel">
          <el-card class="config-card">
            <template #header>
              <div class="card-header">
                <div class="header-left">
                  <el-icon><Setting /></el-icon>
                  <span>试卷配置</span>
                </div>
                <div class="header-actions">
                  <el-button type="primary" @click="generateExam" :loading="generating">
                    <el-icon><MagicStick /></el-icon>
                    {{ generating ? '生成中...' : '生成试卷' }}
                  </el-button>
                </div>
              </div>
            </template>

            <el-form 
              ref="formRef" 
              :model="form" 
              :rules="rules" 
              label-width="100px"
              label-position="top"
            >
              <el-form-item label="试卷名称" prop="examName">
                <el-input 
                  v-model="form.examName" 
                  placeholder="请输入试卷名称"
                  clearable
                />
              </el-form-item>

              <el-form-item label="知识领域" prop="domain">
                <el-select 
                  v-model="form.domain" 
                  placeholder="请选择知识领域"
                  style="width: 100%"
                >
                  <el-option label="前端开发" value="frontend" />
                  <el-option label="后端开发" value="backend" />
                  <el-option label="数据库" value="database" />
                  <el-option label="算法与数据结构" value="algorithm" />
                  <el-option label="系统设计" value="system" />
                  <el-option label="项目管理" value="management" />
                </el-select>
              </el-form-item>



              <el-form-item label="难度等级" prop="difficulty">
                <el-radio-group v-model="form.difficulty">
                  <el-radio label="初级">初级</el-radio>
                  <el-radio label="中级">中级</el-radio>
                  <el-radio label="高级">高级</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item label="考试时长" prop="duration">
                <el-input-number 
                  v-model="form.duration" 
                  :min="30" 
                  :max="180" 
                  :step="15"
                  controls-position="right"
                  style="width: 100%"
                />
                <span class="input-suffix">分钟</span>
              </el-form-item>

              <el-form-item label="考试总分" prop="totalScore">
                <el-input-number 
                  v-model="form.totalScore" 
                  :min="50" 
                  :max="200" 
                  :step="10"
                  controls-position="right"
                  style="width: 100%"
                />
                <span class="input-suffix">分</span>
              </el-form-item>

              <el-form-item label="题目类型">
                <el-checkbox-group v-model="form.questionTypes">
                  <el-checkbox label="单选题">单选题</el-checkbox>
                  <el-checkbox label="多选题">多选题</el-checkbox>
                  <el-checkbox label="判断题">判断题</el-checkbox>
                  <el-checkbox label="填空题">填空题</el-checkbox>
                  <el-checkbox label="简答题">简答题</el-checkbox>
                  <el-checkbox label="编程题">编程题</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-form-item label="题目数量配置">
                <div class="question-config">
                  <div v-if="form.questionTypes.includes('单选题')" class="config-item">
                    <span>单选题：</span>
                    <el-input-number 
                      v-model="form.questionCounts.single" 
                      :min="0" 
                      :max="50"
                      size="small"
                    />
                    <span>题</span>
                  </div>
                  <div v-if="form.questionTypes.includes('多选题')" class="config-item">
                    <span>多选题：</span>
                    <el-input-number 
                      v-model="form.questionCounts.multiple" 
                      :min="0" 
                      :max="20"
                      size="small"
                    />
                    <span>题</span>
                  </div>
                  <div v-if="form.questionTypes.includes('判断题')" class="config-item">
                    <span>判断题：</span>
                    <el-input-number 
                      v-model="form.questionCounts.judge" 
                      :min="0" 
                      :max="30"
                      size="small"
                    />
                    <span>题</span>
                  </div>
                  <div v-if="form.questionTypes.includes('填空题')" class="config-item">
                    <span>填空题：</span>
                    <el-input-number 
                      v-model="form.questionCounts.fill" 
                      :min="0" 
                      :max="20"
                      size="small"
                    />
                    <span>题</span>
                  </div>
                  <div v-if="form.questionTypes.includes('简答题')" class="config-item">
                    <span>简答题：</span>
                    <el-input-number 
                      v-model="form.questionCounts.short" 
                      :min="0" 
                      :max="10"
                      size="small"
                    />
                    <span>题</span>
                  </div>
                  <div v-if="form.questionTypes.includes('编程题')" class="config-item">
                    <span>编程题：</span>
                    <el-input-number 
                      v-model="form.questionCounts.coding" 
                      :min="0" 
                      :max="5"
                      size="small"
                    />
                    <span>题</span>
                  </div>
                </div>
              </el-form-item>



              <el-form-item label="特殊要求">
                <el-input
                  v-model="form.specialRequirements"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入特殊要求或补充说明"
                />
              </el-form-item>

              <el-form-item label="选择文件" prop="knowledgeFiles">
                <div v-if="form.knowledgeFiles.length === 0" class="empty-files">
                  <el-empty description="暂未选择知识库文件" :image-size="60">
                    <el-button type="primary" size="small" @click="showKnowledgeDialog = true">
                      选择文件
                    </el-button>
                  </el-empty>
                </div>
                
                <div v-else class="selected-files">
                  <div 
                    v-for="file in form.knowledgeFiles" 
                    :key="file.id"
                    class="file-item"
                  >
                    <div class="file-info">
                      <el-icon class="file-icon">
                        <Document v-if="file.type === 'pdf'" />
                        <DocumentCopy v-else-if="file.type === 'doc'" />
                        <Memo v-else />
                      </el-icon>
                      <div class="file-details">
                        <span class="file-name">{{ file.name }}</span>
                        <span class="file-meta">{{ file.size }} | {{ file.uploadTime }}</span>
                      </div>
                    </div>
                    <div class="file-actions">
                      <el-tag :type="getFileTypeTag(file.type)" size="small">
                        {{ file.type.toUpperCase() }}
                      </el-tag>
                      <el-button 
                        size="small" 
                        type="danger" 
                        text 
                        @click="removeKnowledgeFile(file.id)"
                      >
                        <el-icon><Close /></el-icon>
                      </el-button>
                    </div>
                  </div>
                  <div class="add-more-files">
                    <el-button size="small" @click="showKnowledgeDialog = true">
                      <el-icon><Plus /></el-icon>
                      继续添加
                    </el-button>
                  </div>
                </div>
              </el-form-item>
            </el-form>
          </el-card>
        </div>

        <!-- 右侧预览面板 -->
        <div class="preview-panel">
          <el-card class="preview-card">
            <template #header>
              <div class="card-header">
                <el-icon><View /></el-icon>
                <span>试卷预览</span>
                <div class="header-actions" v-if="generatedExam">
                  <el-button size="small" @click="exportExam">
                    <el-icon><Download /></el-icon>
                    导出
                  </el-button>
                  <el-button size="small" type="primary" @click="saveExam">
                    <el-icon><Check /></el-icon>
                    保存
                  </el-button>
                </div>
              </div>
            </template>

            <div class="preview-content">
              <div v-if="!generatedExam && !generating" class="empty-state">
                <el-icon class="empty-icon"><EditPen /></el-icon>
                <p>请配置试卷参数，然后点击"生成试卷"按钮</p>
              </div>

              <div v-if="generating" class="loading-state">
                <el-icon class="loading-icon"><Loading /></el-icon>
                <p>AI正在为您生成专业试卷...</p>
                <div class="loading-tips">
                  <p>🔍 分析知识库内容</p>
                  <p>📝 生成题目内容</p>
                  <p>⚖️ 平衡难度分布</p>
                  <p>✅ 优化试卷结构</p>
                </div>
              </div>

              <div v-if="generatedExam" class="exam-content">
                <div class="exam-header">
                  <h2>{{ form.examName }}</h2>
                  <div class="exam-info">
                    <span>考试时长：{{ form.duration }}分钟</span>
                    <span>总分：{{ generatedExam.totalScore }}分</span>
                    <span>题目数量：{{ generatedExam.totalQuestions }}题</span>
                  </div>
                </div>

                <div class="exam-sections">
                  <div 
                    v-for="section in generatedExam.sections" 
                    :key="section.type"
                    class="exam-section"
                  >
                    <h3>{{ section.title }}（共{{ section.questions.length }}题，{{ section.score }}分）</h3>
                    
                    <div class="questions-list">
                      <div 
                        v-for="(question, index) in section.questions" 
                        :key="index"
                        class="question-item"
                      >
                        <div class="question-header">
                          <span class="question-number">{{ index + 1 }}.</span>
                          <span class="question-score">（{{ question.score }}分）</span>
                        </div>
                        <div class="question-content">
                          <p class="question-text">{{ question.content }}</p>
                          
                          <div v-if="question.options" class="question-options">
                            <div 
                              v-for="(option, optIndex) in question.options" 
                              :key="optIndex"
                              class="option-item"
                            >
                              <span class="option-label">{{ String.fromCharCode(65 + optIndex) }}.</span>
                              <span>{{ option }}</span>
                            </div>
                          </div>
                          
                          <div v-if="question.type === '填空题'" class="fill-blanks">
                            <p>请在横线处填入正确答案：</p>
                            <div class="blank-line">_________________</div>
                          </div>
                          
                          <div v-if="question.type === '简答题'" class="answer-area">
                            <p>答题区域：</p>
                            <div class="answer-box"></div>
                          </div>
                          
                          <div v-if="question.type === '编程题'" class="coding-area">
                            <p>编程要求：{{ question.requirement }}</p>
                            <div class="code-template">
                              <pre>{{ question.template }}</pre>
                            </div>
                          </div>
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
  </div>

  <!-- 知识库文件选择对话框 -->
  <el-dialog
    v-model="showKnowledgeDialog"
    title="选择知识库文件"
    width="800px"
    :before-close="handleKnowledgeDialogClose"
  >
    <div class="knowledge-dialog-content">
      <div class="dialog-header">
        <div class="search-section">
          <el-input
            v-model="knowledgeSearch"
            placeholder="搜索文件名..."
            clearable
            @input="filterKnowledgeFiles"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="filter-section">
          <el-select v-model="knowledgeTypeFilter" placeholder="文件类型" clearable>
            <el-option label="全部类型" value="" />
            <el-option label="PDF" value="pdf" />
            <el-option label="Word" value="doc" />
            <el-option label="文本" value="txt" />
            <el-option label="Markdown" value="md" />
          </el-select>
        </div>
      </div>

      <div class="knowledge-files-list">
        <div v-if="filteredKnowledgeFiles.length === 0" class="empty-knowledge">
          <el-empty description="暂无可用的知识库文件">
            <el-button type="primary" @click="uploadKnowledgeFile">
              <el-icon><Upload /></el-icon>
              上传文件
            </el-button>
          </el-empty>
        </div>

        <div v-else class="files-grid">
          <div
            v-for="file in filteredKnowledgeFiles"
            :key="file.id"
            class="knowledge-file-item"
            :class="{ selected: selectedKnowledgeFiles.includes(file.id) }"
            @click="toggleKnowledgeFile(file)"
          >
            <div class="file-checkbox">
              <el-checkbox
                :model-value="selectedKnowledgeFiles.includes(file.id)"
                @change="toggleKnowledgeFile(file)"
              />
            </div>
            
            <div class="file-icon-large">
              <el-icon>
                <Document v-if="file.type === 'pdf'" />
                <DocumentCopy v-else-if="file.type === 'doc'" />
                <Memo v-else />
              </el-icon>
            </div>
            
            <div class="file-info-detailed">
              <h4 class="file-title">{{ file.name }}</h4>
              <p class="file-description">{{ file.description || '暂无描述' }}</p>
              <div class="file-metadata">
                <span class="file-size">{{ file.size }}</span>
                <span class="file-date">{{ file.uploadTime }}</span>
                <el-tag :type="getFileTypeTag(file.type)" size="small">
                  {{ file.type.toUpperCase() }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <div class="selected-count">
          已选择 {{ selectedKnowledgeFiles.length }} 个文件
        </div>
        <div class="footer-actions">
          <el-button @click="showKnowledgeDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmKnowledgeSelection">
            确认选择
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  MagicStick, EditPen, Refresh, Files, Plus, Clock, Document, Star, 
  View, Edit, CopyDocument, Delete, Setting, Close, Check, 
  Search, Upload 
} from '@element-plus/icons-vue'

// 响应式数据
const formRef = ref()
const generating = ref(false)
const generatedExam = ref(null)

// 试卷列表相关
const savedExams = ref([])
const selectedExam = ref(null)

// 知识库文件相关
const showKnowledgeDialog = ref(false)
const knowledgeSearch = ref('')
const knowledgeTypeFilter = ref('')
const selectedKnowledgeFiles = ref([])
const availableKnowledgeFiles = ref([])
const filteredKnowledgeFiles = ref([])

// 表单数据
const form = reactive({
  examName: '',
  domain: '',
  difficulty: '中级',
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
  domain: [
    { required: true, message: '请选择知识领域', trigger: 'change' }
  ],
  totalScore: [
    { required: true, message: '请设置考试总分', trigger: 'blur' },
    { type: 'number', min: 50, max: 200, message: '总分应在50-200分之间', trigger: 'blur' }
  ]
}



// 生成试卷
const generateExam = async () => {
  try {
    await formRef.value.validate()
    
    if (form.questionTypes.length === 0) {
      ElMessage.warning('请至少选择一种题目类型')
      return
    }
    
    generating.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 4000))
    
    // 模拟生成的试卷内容
    generatedExam.value = {
      totalScore: 100,
      totalQuestions: getTotalQuestions(),
      sections: generateSections()
    }
    
    ElMessage.success('试卷生成成功！')
  } catch (error) {
    console.error('生成试卷失败:', error)
    ElMessage.error('生成试卷失败，请重试')
  } finally {
    generating.value = false
  }
}

// 计算总题目数
const getTotalQuestions = () => {
  return Object.values(form.questionCounts).reduce((sum, count) => sum + count, 0)
}

// 生成试卷章节
const generateSections = () => {
  const sections = []
  
  if (form.questionTypes.includes('单选题') && form.questionCounts.single > 0) {
    sections.push({
      type: 'single',
      title: '一、单选题',
      score: form.questionCounts.single * 2,
      questions: generateQuestions('单选题', form.questionCounts.single, 2)
    })
  }
  
  if (form.questionTypes.includes('多选题') && form.questionCounts.multiple > 0) {
    sections.push({
      type: 'multiple',
      title: '二、多选题',
      score: form.questionCounts.multiple * 3,
      questions: generateQuestions('多选题', form.questionCounts.multiple, 3)
    })
  }
  
  if (form.questionTypes.includes('判断题') && form.questionCounts.judge > 0) {
    sections.push({
      type: 'judge',
      title: '三、判断题',
      score: form.questionCounts.judge * 1,
      questions: generateQuestions('判断题', form.questionCounts.judge, 1)
    })
  }
  
  if (form.questionTypes.includes('填空题') && form.questionCounts.fill > 0) {
    sections.push({
      type: 'fill',
      title: '四、填空题',
      score: form.questionCounts.fill * 3,
      questions: generateQuestions('填空题', form.questionCounts.fill, 3)
    })
  }
  
  if (form.questionTypes.includes('简答题') && form.questionCounts.short > 0) {
    sections.push({
      type: 'short',
      title: '五、简答题',
      score: form.questionCounts.short * 10,
      questions: generateQuestions('简答题', form.questionCounts.short, 10)
    })
  }
  
  if (form.questionTypes.includes('编程题') && form.questionCounts.coding > 0) {
    sections.push({
      type: 'coding',
      title: '六、编程题',
      score: form.questionCounts.coding * 20,
      questions: generateQuestions('编程题', form.questionCounts.coding, 20)
    })
  }
  
  return sections
}

// 生成题目
const generateQuestions = (type, count, score) => {
  const questions = []
  
  for (let i = 0; i < count; i++) {
    const question = {
      type,
      score,
      content: getQuestionContent(type, i + 1)
    }
    
    if (type === '单选题' || type === '多选题') {
      question.options = getQuestionOptions(type)
    }
    
    if (type === '编程题') {
      question.requirement = '请实现一个函数，完成指定功能'
      question.template = 'function solution() {\n  // 请在此处编写代码\n  \n}'
    }
    
    questions.push(question)
  }
  
  return questions
}

// 获取题目内容
const getQuestionContent = (type, index) => {
  const contents = {
    '单选题': [
      '以下哪个是Vue.js的核心特性？',
      'JavaScript中哪个方法用于数组遍历？',
      'CSS中用于设置元素浮动的属性是？'
    ],
    '多选题': [
      '以下哪些是前端框架？（多选）',
      'HTTP状态码中表示成功的有哪些？（多选）',
      'JavaScript的数据类型包括哪些？（多选）'
    ],
    '判断题': [
      'Vue.js是一个渐进式JavaScript框架。',
      'CSS中的margin属性会影响元素的实际大小。',
      'JavaScript是一种编译型语言。'
    ],
    '填空题': [
      'Vue.js中用于双向数据绑定的指令是 ______。',
      'CSS中设置元素宽度的属性是 ______。',
      'JavaScript中声明变量的关键字有 ______ 和 ______。'
    ],
    '简答题': [
      '请简述Vue.js的生命周期钩子函数。',
      '解释CSS盒模型的概念。',
      '什么是JavaScript的闭包？请举例说明。'
    ],
    '编程题': [
      '实现一个函数，判断一个字符串是否为回文。',
      '编写一个函数，实现数组去重功能。',
      '实现一个简单的防抖函数。'
    ]
  }
  
  const typeContents = contents[type] || []
  return typeContents[index % typeContents.length] || `${type}示例题目 ${index}`
}

// 获取选项
const getQuestionOptions = (type) => {
  if (type === '单选题') {
    return [
      '响应式数据绑定',
      '组件化开发',
      '虚拟DOM',
      '以上都是'
    ]
  } else if (type === '多选题') {
    return [
      'Vue.js',
      'React',
      'Angular',
      'jQuery'
    ]
  }
  return []
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  generatedExam.value = null
  Object.assign(form, {
    examName: '',
    domain: '',
    difficulty: '中级',
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
}

// 导出试卷
const exportExam = () => {
  ElMessage.success('试卷导出成功')
}

// 保存试卷
const saveExam = () => {
  ElMessage.success('试卷保存成功')
}

// 试卷列表相关方法
const refreshExamList = () => {
  // 模拟获取已保存的试卷列表
  savedExams.value = [
    {
      id: 1,
      name: 'JavaScript基础测试',
      domain: '前端开发',
      difficulty: '初级',
      duration: 60,
      totalQuestions: 20,
      totalScore: 100,
      createdAt: '2024-01-15 10:30:00'
    },
    {
      id: 2,
      name: 'Vue.js进阶考试',
      domain: '前端开发',
      difficulty: '中级',
      duration: 90,
      totalQuestions: 25,
      totalScore: 120,
      createdAt: '2024-01-14 14:20:00'
    },
    {
      id: 3,
      name: 'Node.js后端开发',
      domain: '后端开发',
      difficulty: '高级',
      duration: 120,
      totalQuestions: 30,
      totalScore: 150,
      createdAt: '2024-01-13 09:15:00'
    }
  ]
}

const selectExam = (exam) => {
  selectedExam.value = exam
}

const previewExam = (exam) => {
  ElMessage.info(`预览试卷：${exam.name}`)
}

const editExam = (exam) => {
  // 将试卷数据填充到表单中
  form.examName = exam.name
  form.domain = exam.domain
  form.difficulty = exam.difficulty
  form.duration = exam.duration
  selectedExam.value = exam
  scrollToConfig()
}

const duplicateExam = (exam) => {
  const newExam = { ...exam, id: Date.now(), name: `${exam.name} - 副本` }
  savedExams.value.unshift(newExam)
  ElMessage.success('试卷复制成功')
}

const deleteExam = (exam) => {
  const index = savedExams.value.findIndex(e => e.id === exam.id)
  if (index > -1) {
    savedExams.value.splice(index, 1)
    ElMessage.success('试卷删除成功')
  }
}

const scrollToConfig = () => {
  document.querySelector('.config-panel')?.scrollIntoView({ behavior: 'smooth' })
}

const getDifficultyType = (difficulty) => {
  const types = {
    '初级': 'success',
    '中级': 'warning',
    '高级': 'danger'
  }
  return types[difficulty] || 'info'
}

const formatTime = (timeStr) => {
  return timeStr.split(' ')[0]
}

// 知识库文件相关方法
const initKnowledgeFiles = () => {
  // 模拟可用的知识库文件
  availableKnowledgeFiles.value = [
    {
      id: 1,
      name: 'JavaScript核心概念.pdf',
      type: 'pdf',
      size: '2.5MB',
      uploadTime: '2024-01-10',
      description: 'JavaScript基础语法和核心概念详解'
    },
    {
      id: 2,
      name: 'Vue.js开发指南.doc',
      type: 'doc',
      size: '1.8MB',
      uploadTime: '2024-01-09',
      description: 'Vue.js框架开发完整指南'
    },
    {
      id: 3,
      name: '算法与数据结构.md',
      type: 'md',
      size: '850KB',
      uploadTime: '2024-01-08',
      description: '常用算法和数据结构实现'
    },
    {
      id: 4,
      name: 'Node.js后端开发.pdf',
      type: 'pdf',
      size: '3.2MB',
      uploadTime: '2024-01-07',
      description: 'Node.js服务端开发技术栈'
    },
    {
      id: 5,
      name: '数据库设计原理.txt',
      type: 'txt',
      size: '1.2MB',
      uploadTime: '2024-01-06',
      description: '关系型数据库设计原理和最佳实践'
    }
  ]
  filteredKnowledgeFiles.value = [...availableKnowledgeFiles.value]
}

const filterKnowledgeFiles = () => {
  let filtered = [...availableKnowledgeFiles.value]
  
  // 按文件名搜索
  if (knowledgeSearch.value) {
    filtered = filtered.filter(file => 
      file.name.toLowerCase().includes(knowledgeSearch.value.toLowerCase())
    )
  }
  
  // 按文件类型筛选
  if (knowledgeTypeFilter.value) {
    filtered = filtered.filter(file => file.type === knowledgeTypeFilter.value)
  }
  
  filteredKnowledgeFiles.value = filtered
}

const toggleKnowledgeFile = (file) => {
  const index = selectedKnowledgeFiles.value.indexOf(file.id)
  if (index > -1) {
    selectedKnowledgeFiles.value.splice(index, 1)
  } else {
    selectedKnowledgeFiles.value.push(file.id)
  }
}

const confirmKnowledgeSelection = () => {
  const selectedFiles = availableKnowledgeFiles.value.filter(file => 
    selectedKnowledgeFiles.value.includes(file.id)
  )
  form.knowledgeFiles = selectedFiles
  showKnowledgeDialog.value = false
  ElMessage.success(`已选择 ${selectedFiles.length} 个知识库文件`)
}

const removeKnowledgeFile = (fileId) => {
  const index = form.knowledgeFiles.findIndex(file => file.id === fileId)
  if (index > -1) {
    form.knowledgeFiles.splice(index, 1)
  }
}

const handleKnowledgeDialogClose = () => {
  selectedKnowledgeFiles.value = form.knowledgeFiles.map(file => file.id)
  showKnowledgeDialog.value = false
}

const uploadKnowledgeFile = () => {
  ElMessage.info('上传功能开发中...')
}

const getFileTypeTag = (type) => {
  const tags = {
    'pdf': 'danger',
    'doc': 'primary',
    'txt': 'info',
    'md': 'success'
  }
  return tags[type] || 'info'
}

// 初始化数据
refreshExamList()
initKnowledgeFiles()
</script>

<style lang="scss" scoped>
.exam-generator {
  height: 100%;
  overflow-y: auto;
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

.content-grid {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 24px;
  height: calc(100vh - 200px);
}

.config-panel {
  .config-card {
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
      height: calc(100% - 60px);
      overflow-y: auto;
      padding: 24px;
    }
  }
}

.preview-panel {
  .preview-card {
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
      height: calc(100% - 60px);
      overflow-y: auto;
      padding: 24px;
    }
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  font-weight: 600;
  color: #1e293b;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .el-icon {
      font-size: 18px;
      color: #667eea;
    }
  }
  
  .header-actions {
    display: flex;
    gap: 8px;
    
    .el-button {
      border-radius: 8px;
      font-weight: 500;
      
      &.el-button--primary {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border: none;
      }
    }
  }
}

// 表单样式优化
:deep(.el-form) {
  .el-form-item {
    margin-bottom: 20px;
    
    .el-form-item__label {
      color: #374151;
      font-weight: 600;
      margin-bottom: 8px;
    }
  }
  
  .el-input__wrapper {
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    
    &:hover {
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
    
    &.is-focus {
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
    }
  }
  
  .el-select {
    .el-input__wrapper {
      border-radius: 8px;
    }
  }
  
  .el-radio-group {
    .el-radio {
      margin-right: 20px;
      
      .el-radio__label {
        color: #374151;
        font-weight: 500;
      }
    }
  }
  
  .el-checkbox-group {
    .el-checkbox {
      margin-right: 16px;
      margin-bottom: 8px;
      
      .el-checkbox__label {
        color: #374151;
        font-weight: 500;
      }
    }
  }
  
  .el-input-number {
    .el-input__wrapper {
      border-radius: 8px;
    }
  }
  
  .el-textarea__inner {
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    
    &:hover {
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
  }
}

.input-suffix {
  margin-left: 8px;
  color: #64748b;
  font-size: 14px;
}

.question-config {
  .config-item {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    padding: 12px;
    background: linear-gradient(135deg, rgba(248, 250, 252, 0.8), rgba(241, 245, 249, 0.8));
    border-radius: 8px;
    border: 1px solid rgba(226, 232, 240, 0.5);
    
    span {
      color: #374151;
      font-weight: 500;
      
      &:first-child {
        min-width: 60px;
      }
      
      &:last-child {
        margin-left: 4px;
      }
    }
    
    .el-input-number {
      width: 80px;
    }
  }
}

.preview-content {
  height: 100%;
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #64748b;
    
    .empty-icon {
      font-size: 64px;
      color: #cbd5e1;
      margin-bottom: 16px;
    }
    
    p {
      font-size: 16px;
      margin: 0;
    }
  }
  
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #64748b;
    
    .loading-icon {
      font-size: 48px;
      color: #667eea;
      margin-bottom: 16px;
      animation: rotate 2s linear infinite;
    }
    
    p {
      font-size: 18px;
      font-weight: 600;
      margin: 0 0 24px 0;
      color: #374151;
    }
    
    .loading-tips {
      text-align: center;
      
      p {
        margin: 8px 0;
        font-size: 14px;
        font-weight: 400;
        opacity: 0.8;
      }
    }
  }
}

.exam-content {
  .exam-header {
    text-align: center;
    margin-bottom: 24px;
    padding: 20px;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
    border-radius: 12px;
    border: 1px solid rgba(102, 126, 234, 0.2);
    
    h2 {
      font-size: 24px;
      font-weight: 700;
      background: linear-gradient(135deg, #667eea, #764ba2);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0 0 12px 0;
    }
    
    .exam-info {
      display: flex;
      justify-content: center;
      gap: 24px;
      color: #64748b;
      font-size: 14px;
      font-weight: 500;
      
      span {
        padding: 4px 12px;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 6px;
        border: 1px solid rgba(226, 232, 240, 0.5);
      }
    }
  }
  
  .exam-sections {
    .exam-section {
      margin-bottom: 32px;
      
      h3 {
        font-size: 18px;
        font-weight: 600;
        color: #1e293b;
        margin: 0 0 16px 0;
        padding: 12px 16px;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border-radius: 8px;
        border-left: 4px solid #667eea;
      }
    }
  }
}

.questions-list {
  .question-item {
    margin-bottom: 24px;
    padding: 20px;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(248, 250, 252, 0.9));
    border: 1px solid rgba(226, 232, 240, 0.5);
    border-radius: 12px;
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
      border-color: rgba(102, 126, 234, 0.3);
    }
    
    .question-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      
      .question-number {
        font-weight: 600;
        color: #667eea;
        font-size: 16px;
      }
      
      .question-score {
        color: #64748b;
        font-size: 12px;
        background: rgba(102, 126, 234, 0.1);
        padding: 2px 8px;
        border-radius: 4px;
      }
    }
    
    .question-content {
      .question-text {
        color: #374151;
        line-height: 1.6;
        margin: 0 0 12px 0;
        font-weight: 500;
      }
      
      .question-options {
        .option-item {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          margin-bottom: 8px;
          color: #374151;
          padding: 8px 12px;
          background: rgba(248, 250, 252, 0.8);
          border-radius: 6px;
          border: 1px solid rgba(226, 232, 240, 0.5);
          
          .option-label {
            font-weight: 600;
            min-width: 20px;
            color: #667eea;
          }
        }
      }
      
      .fill-blanks {
        .blank-line {
          border-bottom: 2px solid #667eea;
          width: 200px;
          height: 20px;
          margin: 8px 0;
        }
      }
      
      .answer-area {
        .answer-box {
          border: 2px dashed #cbd5e1;
          min-height: 80px;
          border-radius: 8px;
          margin-top: 8px;
          background: rgba(248, 250, 252, 0.5);
        }
      }
      
      .coding-area {
        .code-template {
          background: linear-gradient(135deg, #1e293b, #334155);
          border-radius: 8px;
          padding: 16px;
          margin-top: 8px;
          border: 1px solid rgba(102, 126, 234, 0.3);
          
          pre {
            margin: 0;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            color: #e2e8f0;
            line-height: 1.5;
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
  .exam-generator {
    padding: 12px;
  }
  
  .content-grid {
    grid-template-columns: 1fr;
    height: auto;
    gap: 16px;
  }
  
  .config-card,
  .preview-card {
    height: auto;
    
    :deep(.el-card__body) {
      height: auto;
    }
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    padding: 20px;
    
    .header-actions {
      width: 100%;
      justify-content: center;
    }
  }
  
  .exam-info {
    flex-direction: column !important;
    gap: 8px !important;
    
    span {
      text-align: center;
    }
  }
}

// 试卷列表样式
.exam-list-section {
  margin-bottom: 24px;
  
  .exam-list-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .header-left {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        color: #1e293b;
        
        .el-icon {
          color: #667eea;
        }
      }
    }
  }
  
  .exam-list-content {
    .empty-exam-list {
      padding: 40px 20px;
      text-align: center;
    }
    
    .exam-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 16px;
      
      .exam-item {
        background: #f8fafc;
        border: 2px solid transparent;
        border-radius: 12px;
        padding: 16px;
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover {
          border-color: #667eea;
          transform: translateY(-2px);
          box-shadow: 0 4px 20px rgba(102, 126, 234, 0.15);
        }
        
        &.active {
          border-color: #667eea;
          background: rgba(102, 126, 234, 0.05);
        }
        
        .exam-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
          
          .exam-title {
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
            margin: 0;
            flex: 1;
          }
        }
        
        .exam-info {
          display: flex;
          gap: 16px;
          margin-bottom: 12px;
          
          .info-item {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            color: #64748b;
            
            .el-icon {
              font-size: 14px;
            }
          }
        }
        
        .exam-meta {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          font-size: 12px;
          color: #64748b;
          
          .domain {
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
            padding: 2px 8px;
            border-radius: 6px;
          }
        }
        
        .exam-actions {
          display: flex;
          gap: 8px;
          
          .el-button {
            flex: 1;
            font-size: 12px;
            padding: 6px 8px;
          }
        }
      }
    }
  }
}

// 知识库文件选择样式
.knowledge-files-section {
  .files-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    .section-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      color: #1e293b;
      
      .el-icon {
        color: #667eea;
      }
    }
  }
  
  .empty-files {
    padding: 20px;
    text-align: center;
  }
  
  .selected-files {
    .file-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      margin-bottom: 8px;
      
      .file-info {
        display: flex;
        align-items: center;
        gap: 12px;
        flex: 1;
        
        .file-icon {
          font-size: 20px;
          color: #667eea;
        }
        
        .file-details {
          .file-name {
            display: block;
            font-weight: 500;
            color: #1e293b;
            margin-bottom: 4px;
          }
          
          .file-meta {
            font-size: 12px;
            color: #64748b;
          }
        }
      }
      
      .file-actions {
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }
    
    .add-more-files {
      margin-top: 12px;
      text-align: center;
      padding: 12px;
      border: 2px dashed #d1d5db;
      border-radius: 8px;
      background: #f9fafb;
      
      &:hover {
        border-color: #667eea;
        background: rgba(102, 126, 234, 0.05);
      }
    }
  }
}

// 知识库对话框样式
.knowledge-dialog-content {
  .dialog-header {
    display: flex;
    gap: 16px;
    margin-bottom: 20px;
    
    .search-section {
      flex: 1;
    }
    
    .filter-section {
      width: 150px;
    }
  }
  
  .knowledge-files-list {
    max-height: 400px;
    overflow-y: auto;
    
    .empty-knowledge {
      padding: 40px 20px;
      text-align: center;
    }
    
    .files-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 16px;
      
      .knowledge-file-item {
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover {
          border-color: #667eea;
          transform: translateY(-2px);
        }
        
        &.selected {
          border-color: #667eea;
          background: rgba(102, 126, 234, 0.05);
        }
        
        .file-checkbox {
          margin-bottom: 12px;
        }
        
        .file-icon-large {
          text-align: center;
          margin-bottom: 12px;
          
          .el-icon {
            font-size: 32px;
            color: #667eea;
          }
        }
        
        .file-info-detailed {
          .file-title {
            font-size: 14px;
            font-weight: 600;
            color: #1e293b;
            margin: 0 0 8px 0;
            line-height: 1.4;
          }
          
          .file-description {
            font-size: 12px;
            color: #64748b;
            margin: 0 0 12px 0;
            line-height: 1.4;
          }
          
          .file-metadata {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            color: #94a3b8;
            
            .file-size, .file-date {
              margin-right: 8px;
            }
          }
        }
      }
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .selected-count {
    font-size: 14px;
    color: #64748b;
  }
  
  .footer-actions {
    display: flex;
    gap: 12px;
  }
}

@media (max-width: 768px) {
  .exam-list-section {
    .exam-grid {
      grid-template-columns: 1fr;
      
      .exam-item {
        .exam-info {
          flex-wrap: wrap;
          gap: 8px;
        }
        
        .exam-actions {
          flex-wrap: wrap;
          
          .el-button {
            flex: 1 1 calc(50% - 4px);
            min-width: 80px;
          }
        }
      }
    }
  }
  
  .knowledge-files-section {
    .files-header {
      flex-direction: column;
      align-items: stretch;
      gap: 12px;
    }
    
    .selected-files {
      .file-item {
        flex-direction: column;
        align-items: stretch;
        gap: 12px;
        
        .file-actions {
          justify-content: flex-end;
        }
      }
      
      .add-more-files {
        padding: 16px 12px;
      }
    }
  }
  
  .knowledge-dialog-content {
    .dialog-header {
      flex-direction: column;
      gap: 12px;
      
      .filter-section {
        width: 100%;
      }
    }
    
    .files-grid {
      grid-template-columns: 1fr;
    }
  }
  
  .dialog-footer {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
    
    .footer-actions {
      justify-content: center;
    }
  }
  
  .question-config {
    .config-item {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
      
      span:first-child {
        min-width: auto;
      }
    }
  }
  
  .exam-header {
    .exam-info {
      span {
        font-size: 12px;
        padding: 2px 8px;
      }
    }
  }
}
</style>