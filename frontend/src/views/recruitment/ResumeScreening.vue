<template>
  <div class="resume-screening">
    <!-- 筛选条件 - 一行显示 -->
    <div class="filter-section">
      <el-card class="filter-card">
        <el-form 
          ref="filterFormRef" 
          :model="filterForm" 
          label-width="80px"
          class="filter-form"
        >
          <div class="filter-row">
            <div class="filter-item">
              <el-form-item label="选择JD" prop="selectedJD">
                <el-select 
                  v-model="filterForm.selectedJD" 
                  placeholder="请选择JD"
                  @change="handleJDChange"
                  style="width: 200px"
                >
                  <el-option
                    v-for="jd in availableJDs"
                    :key="jd.id"
                    :label="jd.title"
                    :value="jd.id"
                  />
                </el-select>
              </el-form-item>
            </div>
            
            <div class="filter-item">
              <el-form-item label="工作经验">
                <el-select v-model="filterForm.experience" placeholder="请选择" style="width: 120px">
                  <el-option label="不限" value="" />
                  <el-option label="应届生" value="应届生" />
                  <el-option label="1-3年" value="1-3年" />
                  <el-option label="3-5年" value="3-5年" />
                  <el-option label="5-10年" value="5-10年" />
                  <el-option label="10年以上" value="10年以上" />
                </el-select>
              </el-form-item>
            </div>
            
            <div class="filter-item">
              <el-form-item label="学历要求">
                <el-select v-model="filterForm.education" placeholder="请选择" style="width: 120px">
                  <el-option label="不限" value="" />
                  <el-option label="大专" value="大专" />
                  <el-option label="本科" value="本科" />
                  <el-option label="硕士" value="硕士" />
                  <el-option label="博士" value="博士" />
                </el-select>
              </el-form-item>
            </div>
            
            <div class="filter-item">
              <el-form-item label="匹配度">
                <el-select v-model="filterForm.matchScore" placeholder="请选择" style="width: 120px">
                  <el-option label="不限" value="" />
                  <el-option label="<60%" value="<60" />
                  <el-option label="≥60%" value=">=60" />
                  <el-option label="≥70%" value=">=70" />
                  <el-option label="≥80%" value=">=80" />
                  <el-option label="≥90%" value=">=90" />
                </el-select>
              </el-form-item>
            </div>
            
            <div class="filter-actions">
              <el-button @click="resetFilters" size="small">重置</el-button>
              <el-button type="primary" @click="applyFilters" size="small">筛选</el-button>
              <el-button 
                @click="handleUploadClick" 
                size="small"
                type="success"
              >
                <el-icon><Upload /></el-icon>
                上传简历
              </el-button>
              <el-button type="primary" @click="startScreening" :loading="screening" size="small">
                <el-icon><Search /></el-icon>
                {{ screening ? '筛选中...' : '开始筛选' }}
              </el-button>
            </div>
          </div>
        </el-form>
      </el-card>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 筛选进度 -->
      <div v-if="screening" class="screening-progress">
        <el-card class="progress-card">
          <div class="progress-content">
            <div class="progress-header">
              <h3>AI正在分析简历...</h3>
              <p>已处理 {{ processedCount }}/{{ totalCount }} 份简历</p>
            </div>
            <el-progress 
              :percentage="progressPercentage" 
              :stroke-width="8"
              status="success"
            />
            <div class="progress-steps">
              <div class="step" :class="{ active: currentStep >= 1 }">
                <el-icon><Document /></el-icon>
                <span>解析简历内容</span>
              </div>
              <div class="step" :class="{ active: currentStep >= 2 }">
                <el-icon><Search /></el-icon>
                <span>提取关键信息</span>
              </div>
              <div class="step" :class="{ active: currentStep >= 3 }">
                <el-icon><DataAnalysis /></el-icon>
                <span>智能匹配分析</span>
              </div>
              <div class="step" :class="{ active: currentStep >= 4 }">
                <el-icon><Check /></el-icon>
                <span>生成筛选结果</span>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 简历列表 -->
      <div v-if="!screening" class="resume-list">
        <el-card class="list-card">
          <template #header>
            <div class="card-header">
              <div class="list-info">
                <el-icon><Files /></el-icon>
                <span>共找到 {{ filteredResumes.length }} 份简历</span>
                <el-divider direction="vertical" />
                <span>按匹配度排序</span>
              </div>
              <div class="list-actions">
                <el-button-group>
                  <el-button 
                    :type="viewMode === 'card' ? 'primary' : ''" 
                    @click="viewMode = 'card'"
                    size="small"
                  >
                    <el-icon><Grid /></el-icon>
                  </el-button>
                  <el-button 
                    :type="viewMode === 'list' ? 'primary' : ''" 
                    @click="viewMode = 'list'"
                    size="small"
                  >
                    <el-icon><List /></el-icon>
                  </el-button>
                </el-button-group>
              </div>
            </div>
          </template>

          <!-- 卡片视图 -->
          <div v-if="viewMode === 'card'" class="resume-cards">
            <div 
              v-for="resume in filteredResumes" 
              :key="resume.id"
              class="resume-card"
              @click="viewResumeDetail(resume)"
            >
              <div class="card-header">
                <div class="candidate-info">
                  <h3 class="candidate-name">{{ resume.name }}</h3>
                  <p class="candidate-position">{{ resume.currentPosition }}</p>
                </div>
                <div class="match-score">
                  <el-progress 
                    type="circle" 
                    :percentage="resume.matchScore"
                    :width="60"
                    :stroke-width="6"
                    :color="getScoreColor(resume.matchScore)"
                  />
                </div>
              </div>

              <div class="card-content">
                 <div class="resume-json">
                   <pre class="json-display">{{ formatResumeAsJson(resume) }}</pre>
                 </div>
               </div>

            <div class="card-skills">
              <el-tag 
                v-for="skill in resume.skills.slice(0, 4)" 
                :key="skill"
                size="small"
                class="skill-tag"
              >
                {{ skill }}
              </el-tag>
              <span v-if="resume.skills.length > 4" class="more-skills">
                +{{ resume.skills.length - 4 }}
              </span>
            </div>

            <div class="card-footer">
              <div class="highlights">
                <el-tag 
                  v-for="highlight in resume.highlights.slice(0, 2)" 
                  :key="highlight"
                  type="success"
                  size="small"
                  effect="plain"
                >
                  {{ highlight }}
                </el-tag>
              </div>
              <div class="actions">
                <el-button size="small" type="danger" @click.stop="rejectCandidate(resume)">
                  不通过
                </el-button>
                <el-button size="small" type="primary" @click.stop="scheduleInterview(resume)">
                  面试
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 列表视图 -->
          <div v-else class="resume-table">
            <el-table :data="filteredResumes" style="width: 100%">
              <el-table-column prop="name" label="姓名" width="120" />
              <el-table-column prop="currentPosition" label="当前职位" width="150" />
              <el-table-column prop="experience" label="工作经验" width="120" />
              <el-table-column prop="education" label="学历" width="100" />
              <el-table-column prop="location" label="地区" width="120" />
              <el-table-column label="匹配度" width="100">
                <template #default="{ row }">
                  <el-progress 
                    :percentage="row.matchScore"
                    :stroke-width="6"
                    :color="getScoreColor(row.matchScore)"
                  />
                </template>
              </el-table-column>
              <el-table-column label="技能标签" min-width="200">
                <template #default="{ row }">
                  <el-tag 
                    v-for="skill in row.skills.slice(0, 3)" 
                    :key="skill"
                    size="small"
                    class="skill-tag"
                  >
                    {{ skill }}
                  </el-tag>
                  <span v-if="row.skills.length > 3" class="more-skills">
                    +{{ row.skills.length - 3 }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" @click="viewResumeDetail(row)">
                    查看
                  </el-button>
                  <el-button size="small" type="primary" @click="scheduleInterview(row)">
                    面试
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 上传简历对话框 -->
    <el-dialog 
      v-model="showUploadDialog" 
      title="上传简历" 
      width="600px"
      :before-close="handleUploadClose"
    >
      <!-- JD选择区域 -->
      <div class="upload-jd-selection">
        <el-form label-width="80px">
          <el-form-item label="选择JD" required>
            <el-select 
              v-model="uploadForm.selectedJD" 
              placeholder="请选择要匹配的JD"
              style="width: 100%"
              @change="handleUploadJDChange"
            >
              <el-option
                v-for="jd in availableJDs"
                :key="jd.id"
                :label="jd.title"
                :value="jd.id"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 当前选择的JD信息 -->
      <div v-if="uploadForm.selectedJD" class="selected-jd-info">
        <el-alert
          :title="`匹配JD: ${getJDById(uploadForm.selectedJD)?.title}`"
          description="上传的简历将与此JD进行匹配度计算"
          type="success"
          :closable="false"
          show-icon
        />
      </div>

      <el-upload
        ref="uploadRef"
        class="upload-demo"
        drag
        :action="uploadAction"
        :headers="uploadHeaders"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        multiple
        accept=".pdf,.doc,.docx"
        :disabled="!uploadForm.selectedJD"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将简历文件拖拽到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF、DOC、DOCX 格式，单个文件不超过 10MB
            <br>
            <span v-if="!uploadForm.selectedJD" style="color: #f56c6c;">请先选择JD后再上传简历</span>
          </div>
        </template>
      </el-upload>

      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmUpload" :disabled="!uploadForm.selectedJD">确定</el-button>
      </template>
    </el-dialog>

    <!-- 简历详情对话框 -->
    <el-dialog 
      v-model="showDetailDialog" 
      :title="selectedResume?.name + ' - 简历详情'" 
      width="800px"
      top="5vh"
    >
      <div v-if="selectedResume" class="resume-detail">
        <div class="detail-header">
          <div class="candidate-avatar">
            <el-avatar :size="80" :src="selectedResume.avatar">
              {{ selectedResume.name.charAt(0) }}
            </el-avatar>
          </div>
          <div class="candidate-basic">
            <h2>{{ selectedResume.name }}</h2>
            <p class="position">{{ selectedResume.currentPosition }}</p>
            <div class="basic-info">
              <span>{{ selectedResume.age }}岁</span>
              <el-divider direction="vertical" />
              <span>{{ selectedResume.experience }}</span>
              <el-divider direction="vertical" />
              <span>{{ selectedResume.education }}</span>
              <el-divider direction="vertical" />
              <span>{{ selectedResume.location }}</span>
            </div>
          </div>
          <div class="match-info">
            <el-progress 
              type="circle" 
              :percentage="selectedResume.matchScore"
              :width="80"
              :stroke-width="8"
              :color="getScoreColor(selectedResume.matchScore)"
            />
            <p>匹配度</p>
          </div>
        </div>

        <el-divider />

        <div class="detail-content">
          <div class="section">
            <h3>技能标签</h3>
            <div class="skills-container">
              <el-tag 
                v-for="skill in selectedResume.skills" 
                :key="skill"
                class="skill-tag"
              >
                {{ skill }}
              </el-tag>
            </div>
          </div>

          <div class="section">
            <h3>工作经历</h3>
            <div class="experience-list">
              <div 
                v-for="exp in selectedResume.workExperience" 
                :key="exp.id"
                class="experience-item"
              >
                <div class="exp-header">
                  <h4>{{ exp.position }} - {{ exp.company }}</h4>
                  <span class="exp-duration">{{ exp.duration }}</span>
                </div>
                <p class="exp-description">{{ exp.description }}</p>
              </div>
            </div>
          </div>

          <div class="section">
            <h3>教育背景</h3>
            <div class="education-list">
              <div 
                v-for="edu in selectedResume.education" 
                :key="edu.id"
                class="education-item"
              >
                <h4>{{ edu.school }} - {{ edu.major }}</h4>
                <span class="edu-degree">{{ edu.degree }} | {{ edu.duration }}</span>
              </div>
            </div>
          </div>

          <div class="section">
            <h3>AI分析亮点</h3>
            <div class="highlights-list">
              <el-tag 
                v-for="highlight in selectedResume.highlights" 
                :key="highlight"
                type="success"
                effect="plain"
                class="highlight-tag"
              >
                {{ highlight }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button @click="contactCandidate(selectedResume)">联系候选人</el-button>
        <el-button type="primary" @click="scheduleInterview(selectedResume)">安排面试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 响应式数据
const screening = ref(false)
const processedCount = ref(0)
const totalCount = ref(0)
const currentStep = ref(1)
const viewMode = ref('card')
const showUploadDialog = ref(false)
const showDetailDialog = ref(false)
const selectedResume = ref(null)
const uploadRef = ref()

// 筛选条件
const filterForm = reactive({
  selectedJD: '', // JD选择
  experience: '', // 工作经验
  education: '', // 学历要求
  matchScore: '' // 匹配度选择项
})

// 上传表单
const uploadForm = reactive({
  selectedJD: '' // 上传时选择的JD
})

// 保留原有的filters对象以兼容现有代码
const filters = reactive({
  selectedJD: '', // 新增JD选择
  position: '',
  experience: '',
  education: '',
  skills: '',
  matchScore: 60
})

// 可用的JD列表
const availableJDs = ref([
  {
    id: 1,
    title: '高级前端开发工程师',
    location: '北京',
    requirements: {
      experience: '3-5年',
      education: '本科',
      skills: ['Vue.js', 'React', 'JavaScript', 'TypeScript', 'Node.js'],
      description: '负责前端架构设计和核心功能开发'
    }
  },
  {
    id: 2,
    title: 'React开发工程师',
    location: '上海',
    requirements: {
      experience: '1-3年',
      education: '本科',
      skills: ['React', 'JavaScript', 'Redux', 'Webpack'],
      description: '负责React项目开发和维护'
    }
  },
  {
    id: 3,
    title: '全栈开发工程师',
    location: '深圳',
    requirements: {
      experience: '3-5年',
      education: '本科',
      skills: ['Vue.js', 'Node.js', 'Python', 'MySQL', 'Redis'],
      description: '负责前后端全栈开发'
    }
  }
])

// 当前选中的JD
const selectedJD = ref(null)

// 模拟简历数据
const resumes = ref([
  {
    id: 1,
    name: '张三',
    currentPosition: '前端开发工程师',
    experience: '3-5年',
    education: '本科',
    location: '北京',
    age: 28,
    matchScore: 92,
    skills: ['Vue.js', 'React', 'JavaScript', 'TypeScript', 'Node.js'],
    highlights: ['大厂经验', '项目经验丰富', '技术栈匹配'],
    avatar: '',
    workExperience: [
      {
        id: 1,
        position: '高级前端开发工程师',
        company: '字节跳动',
        duration: '2021.03 - 至今',
        description: '负责抖音前端业务开发，参与核心功能模块设计与实现'
      }
    ],
    education: [
      {
        id: 1,
        school: '北京大学',
        major: '计算机科学与技术',
        degree: '本科',
        duration: '2017-2021'
      }
    ]
  },
  {
    id: 2,
    name: '李四',
    currentPosition: 'React开发工程师',
    experience: '1-3年',
    education: '本科',
    location: '上海',
    age: 25,
    matchScore: 85,
    skills: ['React', 'JavaScript', 'Redux', 'Webpack'],
    highlights: ['学习能力强', '代码质量高'],
    avatar: '',
    workExperience: [
      {
        id: 1,
        position: 'React开发工程师',
        company: '美团',
        duration: '2022.06 - 至今',
        description: '负责美团外卖前端开发，优化用户体验'
      }
    ],
    education: [
      {
        id: 1,
        school: '复旦大学',
        major: '软件工程',
        degree: '本科',
        duration: '2018-2022'
      }
    ]
  }
])

// 计算属性
const progressPercentage = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((processedCount.value / totalCount.value) * 100)
})

const filteredResumes = computed(() => {
  return resumes.value.filter(resume => {
    // JD筛选
    if (filterForm.selectedJD && filterForm.selectedJD !== filters.selectedJD) {
      return false
    }
    
    // 经验筛选
    if (filterForm.experience && resume.experience !== filterForm.experience) {
      return false
    }
    
    // 学历筛选
    if (filterForm.education && resume.education !== filterForm.education) {
      return false
    }
    
    // 匹配度筛选
    if (filterForm.matchScore) {
      const score = resume.matchScore
      switch (filterForm.matchScore) {
        case '<60':
          if (score >= 60) return false
          break
        case '>=60':
          if (score < 60) return false
          break
        case '>=70':
          if (score < 70) return false
          break
        case '>=80':
          if (score < 80) return false
          break
        case '>=90':
          if (score < 90) return false
          break
      }
    }
    
    return true
  }).sort((a, b) => b.matchScore - a.matchScore)
})

// 新增筛选应用方法
const applyFilters = () => {
  // 同步filterForm到filters对象
  filters.selectedJD = filterForm.selectedJD
  filters.experience = filterForm.experience
  filters.education = filterForm.education
  
  ElMessage.success('筛选条件已应用')
}

// 修改重置筛选方法
const resetFilters = () => {
  Object.assign(filterForm, {
    selectedJD: '',
    experience: '',
    education: '',
    matchScore: ''
  })
  
  Object.assign(filters, {
    selectedJD: '',
    position: '',
    experience: '',
    education: '',
    skills: '',
    matchScore: 60
  })
  
  selectedJD.value = null
  ElMessage.info('筛选条件已重置')
}

// 修改JD变更处理方法
const handleJDChange = (jdId) => {
  selectedJD.value = availableJDs.value.find(jd => jd.id === jdId)
  filters.selectedJD = jdId // 同步到filters对象
  
  if (selectedJD.value) {
    ElMessage.success(`已选择JD: ${selectedJD.value.title}`)
    // 重新计算所有简历的匹配度
    recalculateMatchScores()
  }
}

const recalculateMatchScores = () => {
  if (!selectedJD.value) return
  
  resumes.value.forEach(resume => {
    resume.matchScore = calculateMatchScore(resume, selectedJD.value)
  })
  
  ElMessage.info('已根据选定JD重新计算匹配度')
}

const calculateMatchScore = (resume, jd) => {
  let score = 0
  let totalWeight = 0
  
  // 技能匹配 (权重: 40%)
  const skillWeight = 40
  const resumeSkills = resume.skills.map(s => s.toLowerCase())
  const jdSkills = jd.requirements.skills.map(s => s.toLowerCase())
  const matchingSkills = resumeSkills.filter(skill => 
    jdSkills.some(jdSkill => skill.includes(jdSkill) || jdSkill.includes(skill))
  )
  const skillScore = (matchingSkills.length / jdSkills.length) * 100
  score += skillScore * (skillWeight / 100)
  totalWeight += skillWeight
  
  // 经验匹配 (权重: 30%)
  const expWeight = 30
  const expScore = resume.experience === jd.requirements.experience ? 100 : 70
  score += expScore * (expWeight / 100)
  totalWeight += expWeight
  
  // 学历匹配 (权重: 20%)
  const eduWeight = 20
  const eduScore = resume.education === jd.requirements.education ? 100 : 80
  score += eduScore * (eduWeight / 100)
  totalWeight += eduWeight
  
  // 职位相关性 (权重: 10%)
  const posWeight = 10
  const posScore = resume.currentPosition.toLowerCase().includes('前端') || 
                   resume.currentPosition.toLowerCase().includes('react') || 
                   resume.currentPosition.toLowerCase().includes('vue') ? 100 : 60
  score += posScore * (posWeight / 100)
  totalWeight += posWeight
  
  return Math.round(score)
}

const startScreening = async () => {
  if (resumes.value.length === 0) {
    ElMessage.warning('请先上传简历文件')
    return
  }
  
  if (!filters.selectedJD) {
    ElMessage.warning('请先选择要匹配的JD')
    return
  }

  screening.value = true
  processedCount.value = 0
  totalCount.value = resumes.value.length
  currentStep.value = 1

  // 模拟筛选过程
  for (let i = 0; i < 4; i++) {
    currentStep.value = i + 1
    await new Promise(resolve => setTimeout(resolve, 1000))
  }

  // 模拟处理进度
  for (let i = 0; i <= totalCount.value; i++) {
    processedCount.value = i
    await new Promise(resolve => setTimeout(resolve, 200))
  }

  screening.value = false
  ElMessage.success('简历筛选完成！')
}

const getScoreColor = (score) => {
  if (score >= 90) return '#67c23a'
  if (score >= 80) return '#e6a23c'
  if (score >= 70) return '#f56c6c'
  return '#909399'
}

const viewResumeDetail = (resume) => {
  selectedResume.value = resume
  showDetailDialog.value = true
}

const contactCandidate = (resume) => {
  ElMessage.success(`已发送联系邮件给 ${resume.name}`)
}

const scheduleInterview = (resume) => {
   ElMessageBox.confirm(
     `确定要为 ${resume.name} 安排面试吗？`,
     '安排面试',
     {
       confirmButtonText: '确定',
       cancelButtonText: '取消',
       type: 'info'
     }
   ).then(() => {
     ElMessage.success(`已为 ${resume.name} 安排面试`)
   }).catch(() => {
     // 用户取消
   })
 }

 const rejectCandidate = (resume) => {
   ElMessageBox.confirm(
     `确定要将 ${resume.name} 标记为不通过吗？`,
     '不通过确认',
     {
       confirmButtonText: '确定',
       cancelButtonText: '取消',
       type: 'warning'
     }
   ).then(() => {
     ElMessage.success(`已将 ${resume.name} 标记为不通过`)
   }).catch(() => {
     // 用户取消
   })
 }

 const formatResumeAsJson = (resume) => {
   const resumeData = {
     id: resume.id,
     name: resume.name,
     currentPosition: resume.currentPosition,
     experience: resume.experience,
     education: resume.education,
     location: resume.location,
     age: resume.age,
     matchScore: resume.matchScore,
     skills: resume.skills,
     highlights: resume.highlights,
     workExperience: resume.workExperience
   }
   return JSON.stringify(resumeData, null, 2)
 }

const handleUploadClose = () => {
  showUploadDialog.value = false
}

// 新增上传按钮点击处理
const handleUploadClick = () => {
  // 如果筛选条件中已选择JD，则自动填充到上传表单中
  if (filterForm.selectedJD) {
    uploadForm.selectedJD = filterForm.selectedJD
  }
  showUploadDialog.value = true
}

const beforeUpload = (file) => {
  // 检查是否已选择JD
  if (!uploadForm.selectedJD) {
    ElMessage.warning('请先选择要匹配的JD，然后再上传简历')
    return false
  }
  
  const isValidType = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isValidType) {
    ElMessage.error('只能上传 PDF、DOC、DOCX 格式的文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB!')
    return false
  }
  return true
}

const handleUploadSuccess = (response, file) => {
  ElMessage.success(`${file.name} 上传成功`)
  
  // 模拟解析简历并自动打分
  setTimeout(() => {
    const newResume = {
      id: Date.now(),
      name: `候选人${resumes.value.length + 1}`,
      currentPosition: '前端开发工程师',
      experience: '2-3年',
      education: '本科',
      location: '北京',
      age: 26,
      skills: ['Vue.js', 'JavaScript', 'CSS', 'HTML'],
      highlights: ['技术基础扎实', '学习能力强'],
      avatar: '',
      workExperience: [],
      education: []
    }
    
    // 自动计算匹配度
    if (selectedJD.value) {
      newResume.matchScore = calculateMatchScore(newResume, selectedJD.value)
    } else {
      newResume.matchScore = 75
    }
    
    resumes.value.push(newResume)
    ElMessage.success(`简历解析完成，匹配度: ${newResume.matchScore}%`)
  }, 2000)
}

const handleUploadError = (error, file) => {
  ElMessage.error(`${file.name} 上传失败`)
}

const confirmUpload = () => {
  showUploadDialog.value = false
  ElMessage.success('简历上传完成')
}

// 处理上传对话框中的JD选择变化
const handleUploadJDChange = (jdId) => {
  console.log('选择的JD ID:', jdId)
}

// 根据ID获取JD信息
const getJDById = (jdId) => {
  return availableJDs.value.find(jd => jd.id === jdId)
}

onMounted(() => {
  // 组件挂载后的初始化操作
})
</script>

<style lang="scss" scoped>
.resume-screening {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px;
  
  .page-header {
    background: white;
    border-radius: 8px;
    padding: 8px 20px;
    margin-bottom: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      max-width: 1400px;
      margin: 0 auto;
    }
    
    .page-title {
      font-size: 18px;
      font-weight: 600;
      color: #2c3e50;
      margin: 0;
      display: flex;
      align-items: center;
      gap: 6px;
      
      .el-icon {
        color: #667eea;
        font-size: 16px;
      }
    }
    
    .header-actions {
      display: flex;
      gap: 8px;
      
      .el-button {
        height: 28px;
        font-size: 13px;
        padding: 4px 12px;
      }
    }
  }
  
  .filter-section {
    max-width: 1400px;
    margin: 0 auto 12px;
    
    .filter-card {
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
      border: none;
      
      :deep(.el-card__body) {
        padding: 12px 20px;
      }
    }
    
    .filter-form {
      .filter-row {
        display: flex;
        align-items: end;
        gap: 12px;
        flex-wrap: wrap;
        
        .filter-item {
          margin-bottom: 0;
          
          :deep(.el-form-item__label) {
            font-size: 13px;
            font-weight: 500;
            color: #606266;
            margin-bottom: 2px;
          }
        }
        
        .filter-actions {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-left: 16px;
          
          .el-button {
            height: 32px;
            font-size: 13px;
            padding: 6px 12px;
          }
        }
      }
    }
  }
  
  .main-content {
    max-width: 1400px;
    margin: 0 auto;
    
    .screening-progress {
      margin-bottom: 16px;
      
      .progress-card {
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        border: none;
        
        .progress-content {
          .progress-header {
            text-align: center;
            margin-bottom: 20px;
            
            h3 {
              color: #2c3e50;
              margin-bottom: 8px;
            }
            
            p {
              color: #606266;
              margin: 0;
            }
          }
          
          .progress-steps {
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
            
            .step {
              display: flex;
              flex-direction: column;
              align-items: center;
              gap: 8px;
              opacity: 0.5;
              transition: opacity 0.3s;
              
              &.active {
                opacity: 1;
                color: #667eea;
              }
              
              .el-icon {
                font-size: 20px;
              }
              
              span {
                font-size: 12px;
                text-align: center;
              }
            }
          }
        }
      }
    }
    
    .resume-list {
      .list-card {
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        border: none;
        
        :deep(.el-card__header) {
          padding: 16px 24px;
          border-bottom: 1px solid #f0f2f5;
        }
        
        :deep(.el-card__body) {
          padding: 24px;
        }
        
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          
          .list-info {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #606266;
            font-size: 14px;
            
            .el-icon {
              color: #667eea;
            }
          }
          
          .list-actions {
            .el-button-group {
              .el-button {
                padding: 6px 12px;
              }
            }
          }
        }
        
        .resume-cards {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
          gap: 16px;
          
          .resume-card {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
            padding: 16px;
            border: 1px solid rgba(228, 231, 237, 0.5);
            transition: all 0.3s ease;
            cursor: pointer;
            backdrop-filter: blur(5px);
            
            &:hover {
              border-color: #667eea;
              box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
              transform: translateY(-2px);
            }
            
            .card-header {
              display: flex;
              justify-content: space-between;
              align-items: flex-start;
              margin-bottom: 12px;
              
              .candidate-info {
                flex: 1;
                
                .candidate-name {
                  font-size: 16px;
                  font-weight: 600;
                  color: #2c3e50;
                  margin-bottom: 4px;
                }
                
                .candidate-position {
                  font-size: 14px;
                  color: #909399;
                  margin: 0;
                }
              }
              
              .match-score {
                text-align: center;
              }
            }
            
            .card-content {
              margin-bottom: 12px;
              
              .info-row {
                display: flex;
                align-items: center;
                gap: 6px;
                margin-bottom: 6px;
                font-size: 13px;
                color: #606266;
                
                .el-icon {
                  color: #909399;
                  font-size: 14px;
                }
                
                &:last-child {
                  margin-bottom: 0;
                }
              }
            }
            
            .card-skills {
              margin-bottom: 12px;
              
              .skill-tag {
                margin-right: 6px;
                margin-bottom: 6px;
                background: rgba(102, 126, 234, 0.1);
                color: #667eea;
                border: 1px solid rgba(102, 126, 234, 0.3);
              }
              
              .more-skills {
                font-size: 12px;
                color: #909399;
              }
            }
            
            .card-footer {
              display: flex;
              justify-content: space-between;
              align-items: center;
              
              .highlights {
                flex: 1;
                
                .el-tag {
                  margin-right: 6px;
                  font-size: 11px;
                }
              }
              
              .actions {
                display: flex;
                gap: 8px;
                
                .el-button {
                  padding: 4px 12px;
                  font-size: 12px;
                }
              }
            }
            
            .resume-json {
              margin: 16px 0;
            }
            
            .json-display {
              background-color: #f5f5f5;
              border: 1px solid #e0e0e0;
              border-radius: 4px;
              padding: 12px;
              font-family: 'Courier New', monospace;
              font-size: 12px;
              line-height: 1.4;
              color: #333;
              white-space: pre-wrap;
              word-wrap: break-word;
              max-height: 200px;
              overflow-y: auto;
            }
          }
        }
        
        .resume-table {
          :deep(.el-table) {
            background: transparent;
            
            .el-table__header {
              th {
                background: rgba(250, 251, 252, 0.8);
                color: #606266;
                font-weight: 500;
              }
            }
            
            .skill-tag {
              margin-right: 6px;
              margin-bottom: 4px;
              background: rgba(102, 126, 234, 0.1);
              color: #667eea;
              border: 1px solid rgba(102, 126, 234, 0.3);
            }
            
            .more-skills {
              font-size: 12px;
              color: #909399;
            }
          }
        }
      }
    }
  }
  
  // Element Plus 组件样式覆盖
  :deep(.el-button) {
    border-radius: 6px;
    font-weight: 500;
    
    &.el-button--primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-color: #667eea;
      
      &:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
        border-color: #5a6fd8;
      }
    }
  }
  
  :deep(.el-input__wrapper) {
    border-radius: 6px;
    box-shadow: 0 0 0 1px rgba(220, 223, 230, 0.8);
    background: rgba(255, 255, 255, 0.9);
    
    &:hover {
      box-shadow: 0 0 0 1px rgba(192, 196, 204, 0.8);
    }
    
    &.is-focus {
      box-shadow: 0 0 0 1px #667eea;
    }
  }
  
  :deep(.el-select) {
    .el-input__wrapper {
      border-radius: 6px;
    }
  }
  
  :deep(.el-slider) {
    .el-slider__runway {
      background: rgba(228, 231, 237, 0.8);
    }
    
    .el-slider__bar {
      background: #667eea;
    }
    
    .el-slider__button {
      border-color: #667eea;
    }
  }
  
  :deep(.el-progress) {
    .el-progress__text {
      font-size: 12px;
      font-weight: 500;
    }
  }
  
  :deep(.el-card) {
    border: none;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  :deep(.el-dialog) {
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    
    .el-dialog__header {
      padding: 20px 24px 16px;
      border-bottom: 1px solid rgba(240, 242, 245, 0.5);
      
      .el-dialog__title {
        font-size: 18px;
        font-weight: 600;
        color: #2c3e50;
      }
    }
    
    .el-dialog__body {
      padding: 24px;
    }
    
    .el-dialog__footer {
      padding: 16px 24px 20px;
      border-top: 1px solid rgba(240, 242, 245, 0.5);
    }
  }
  
  // 简历详情对话框样式
  .resume-detail {
    .detail-header {
      display: flex;
      gap: 20px;
      margin-bottom: 20px;
      
      .candidate-avatar {
        flex-shrink: 0;
      }
      
      .candidate-basic {
        flex: 1;
        
        h2 {
          margin: 0 0 8px;
          color: #2c3e50;
          font-size: 20px;
        }
        
        .position {
          color: #606266;
          margin: 0 0 12px;
          font-size: 16px;
        }
        
        .basic-info {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #909399;
          font-size: 14px;
        }
      }
      
      .match-info {
        text-align: center;
        
        p {
          margin: 8px 0 0;
          color: #606266;
          font-size: 14px;
        }
      }
    }
    
    .detail-content {
      .section {
        margin-bottom: 24px;
        
        h3 {
          color: #2c3e50;
          font-size: 16px;
          margin-bottom: 12px;
          padding-bottom: 8px;
          border-bottom: 1px solid rgba(240, 242, 245, 0.5);
        }
        
        .skills-container {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          
          .skill-tag {
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
            border: 1px solid rgba(102, 126, 234, 0.3);
          }
        }
        
        .experience-list, .education-list {
          .experience-item, .education-item {
            padding: 12px 0;
            border-bottom: 1px solid rgba(245, 247, 250, 0.5);
            
            &:last-child {
              border-bottom: none;
            }
            
            .exp-header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 8px;
              
              h4 {
                margin: 0;
                color: #2c3e50;
                font-size: 14px;
              }
              
              .exp-duration {
                color: #909399;
                font-size: 13px;
              }
            }
            
            .exp-description {
              color: #606266;
              font-size: 13px;
              line-height: 1.5;
              margin: 0;
            }
            
            .edu-degree {
              color: #909399;
              font-size: 13px;
            }
          }
        }
        
        .highlights-list {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          
          .highlight-tag {
            font-size: 12px;
          }
        }
      }
    }
  }
  
  // 上传对话框样式
  :deep(.upload-demo) {
    .el-upload {
      border: 2px dashed rgba(217, 217, 217, 0.8);
      border-radius: 8px;
      cursor: pointer;
      position: relative;
      overflow: hidden;
      transition: all 0.3s;
      
      &:hover {
        border-color: #667eea;
      }
    }
    
    .el-upload-dragger {
      background: rgba(250, 251, 252, 0.8);
      border: none;
      border-radius: 8px;
      
      &:hover {
        background: rgba(245, 247, 250, 0.8);
      }
    }
    
    .el-icon--upload {
      font-size: 48px;
      color: rgba(192, 196, 204, 0.8);
      margin-bottom: 16px;
    }
    
    .el-upload__text {
      color: #606266;
      font-size: 14px;
      
      em {
        color: #667eea;
        font-style: normal;
      }
    }
    
    .el-upload__tip {
      color: #909399;
      font-size: 12px;
      margin-top: 8px;
    }
  }
  
  // JD选择提示样式
  .jd-selection-notice {
    margin-bottom: 20px;
    
    :deep(.el-alert) {
      border-radius: 8px;
      border: 1px solid #fdf6ec;
      background: rgba(253, 246, 236, 0.8);
      
      .el-alert__icon {
        color: #e6a23c;
      }
      
      .el-alert__title {
        color: #e6a23c;
        font-weight: 600;
      }
      
      .el-alert__description {
        color: #b88230;
        line-height: 1.5;
      }
    }
  }
  
  .selected-jd-info {
    margin-bottom: 20px;
    
    :deep(.el-alert) {
      border-radius: 8px;
      border: 1px solid #f0f9ff;
      background: rgba(240, 249, 255, 0.8);
      
      .el-alert__icon {
        color: #67c23a;
      }
      
      .el-alert__title {
        color: #67c23a;
        font-weight: 600;
      }
      
      .el-alert__description {
        color: #529b2e;
        line-height: 1.5;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .resume-screening {
    padding: 12px;
    
    .page-header {
      .header-content {
        flex-direction: column;
        gap: 12px;
        text-align: center;
      }
    }
    
    .filter-section {
      .filter-form {
        .filter-row {
          flex-direction: column;
          align-items: stretch;
          
          .filter-item {
            width: 100%;
            
            :deep(.el-select),
            :deep(.el-input) {
              width: 100% !important;
            }
          }
          
          .filter-actions {
            justify-content: center;
          }
        }
      }
    }
    
    .main-content {
      .resume-list {
        .list-card {
          .resume-cards {
            grid-template-columns: 1fr;
          }
        }
      }
    }
  }
}

// 动画效果
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

.page-header,
.filter-section,
.main-content {
  animation: fadeInUp 0.6s ease-out;
}

.page-header {
  animation-delay: 0.1s;
}

.filter-section {
  animation-delay: 0.2s;
}

.main-content {
  animation-delay: 0.3s;
}

.resume-card {
  animation: fadeInUp 0.4s ease-out;
}
</style>

const rejectCandidate = (resume) => {
  ElMessageBox.confirm(
    `确定要将 ${resume.name} 标记为不通过吗？`,
    '不通过确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.success(`已将 ${resume.name} 标记为不通过`)
  }).catch(() => {
    // 用户取消
  })
}

const formatResumeAsJson = (resume) => {
  const resumeData = {
    id: resume.id,
    name: resume.name,
    currentPosition: resume.currentPosition,
    experience: resume.experience,
    education: resume.education,
    location: resume.location,
    age: resume.age,
    matchScore: resume.matchScore,
    skills: resume.skills,
    highlights: resume.highlights,
    workExperience: resume.workExperience,
    education: resume.education
  }
  return JSON.stringify(resumeData, null, 2)
}