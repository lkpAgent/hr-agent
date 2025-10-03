<template>
  <div class="smart-interview">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><VideoCamera /></el-icon>
            智能面试
          </h1>
          <p class="page-subtitle">
            AI辅助面试，提供智能问题推荐和候选人评估
          </p>
        </div>
        
        <!-- 筛选区域 -->
        <div class="filter-section">
          <div class="filter-row">
            <div class="filter-item">
              <label class="filter-label">姓名筛选</label>
              <el-input
                v-model="filters.name"
                placeholder="请输入候选人姓名"
                clearable
                size="default"
                style="width: 200px"
                @input="handleFilterChange"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>
            
            <div class="filter-item">
              <label class="filter-label">岗位筛选</label>
              <el-select
                v-model="filters.position"
                placeholder="请选择岗位"
                clearable
                size="default"
                style="width: 200px"
                @change="handleFilterChange"
              >
                <el-option
                  v-for="position in availablePositions"
                  :key="position"
                  :label="position"
                  :value="position"
                />
              </el-select>
            </div>
            
            <div class="filter-actions">
              <el-button @click="clearFilters" size="default">
                <el-icon><RefreshLeft /></el-icon>
                重置筛选
              </el-button>
              <el-tag v-if="filteredCandidatesCount !== totalCandidatesCount" type="info" size="default">
                已筛选 {{ filteredCandidatesCount }} / {{ totalCandidatesCount }} 人
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域：左右分栏布局 -->
    <div class="main-content">
      <!-- 左侧：候选人列表 -->
      <div class="left-panel">
        <el-card class="candidate-list-card">
          <template #header>
            <div class="card-header">
              <span>候选人列表</span>
              <el-button size="small" @click="refreshCandidates">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>

          <div class="candidate-list">
            <div 
              v-for="candidate in filteredCandidates" 
              :key="candidate.id"
              class="candidate-item"
              :class="{ active: selectedCandidate?.id === candidate.id }"
              @click="selectCandidate(candidate)"
            >
              <!-- 候选人基本信息 -->
              <div class="candidate-info">
                <div class="candidate-header">
                  <h3 class="candidate-name">{{ candidate.name }}</h3>
                  <el-tag :type="getScoreType(candidate.totalScore)" size="small">
                    {{ candidate.totalScore }}分
                  </el-tag>
                </div>
                <p class="candidate-position">{{ candidate.position }}</p>
                <div class="candidate-details">
                  <span class="detail-item">{{ candidate.experience }}年经验</span>
                  <span class="detail-item">{{ candidate.education }}</span>
                  <span class="detail-item">{{ candidate.location }}</span>
                </div>
              </div>

              <!-- 打分项 -->
              <div class="score-items">
                <div class="score-row">
                  <div class="score-item">
                    <span class="score-label">技能匹配</span>
                    <el-rate 
                      v-model="candidate.scores.skillMatch" 
                      :max="5" 
                      size="small" 
                      disabled
                      show-score
                    />
                  </div>
                  <div class="score-item">
                    <span class="score-label">工作经验</span>
                    <el-rate 
                      v-model="candidate.scores.experience" 
                      :max="5" 
                      size="small" 
                      disabled
                      show-score
                    />
                  </div>
                </div>
                <div class="score-row">
                  <div class="score-item">
                    <span class="score-label">教育背景</span>
                    <el-rate 
                      v-model="candidate.scores.education" 
                      :max="5" 
                      size="small" 
                      disabled
                      show-score
                    />
                  </div>
                  <div class="score-item">
                    <span class="score-label">综合评价</span>
                    <el-rate 
                      v-model="candidate.scores.overall" 
                      :max="5" 
                      size="small" 
                      disabled
                      show-score
                    />
                  </div>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="candidate-actions">
                <el-button 
                  size="small" 
                  type="primary" 
                  @click.stop="generateInterviewPlan(candidate)"
                  :loading="generatingPlan && selectedCandidate?.id === candidate.id"
                >
                  生成面试方案
                </el-button>
                <el-button size="small" @click.stop="viewResume(candidate)">
                  查看简历
                </el-button>
              </div>
            </div>
            
            <!-- 空状态 -->
            <div v-if="filteredCandidates.length === 0" class="empty-candidates">
              <el-empty 
                description="没有找到符合条件的候选人"
                :image-size="120"
              >
                <el-button type="primary" @click="clearFilters">
                  清除筛选条件
                </el-button>
              </el-empty>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右侧：Tab页内容 -->
      <div class="right-panel">
        <el-card class="content-card">
          <el-tabs v-model="activeTab" class="content-tabs">
            <!-- 简历预览Tab -->
            <el-tab-pane label="简历预览" name="resume">
              <div class="resume-preview">
                <div v-if="!selectedCandidate" class="empty-state">
                  <el-empty description="请选择一个候选人查看简历" />
                </div>
                <div v-else class="resume-content">
                  <!-- 个人信息 -->
                  <div class="resume-section">
                    <h3 class="section-title">个人信息</h3>
                    <div class="personal-info">
                      <div class="info-row">
                        <div class="info-item">
                          <label>姓名：</label>
                          <span>{{ selectedCandidate.resume.personalInfo.name }}</span>
                        </div>
                        <div class="info-item">
                          <label>年龄：</label>
                          <span>{{ selectedCandidate.resume.personalInfo.age }}岁</span>
                        </div>
                      </div>
                      <div class="info-row">
                        <div class="info-item">
                          <label>电话：</label>
                          <span>{{ selectedCandidate.resume.personalInfo.phone }}</span>
                        </div>
                        <div class="info-item">
                          <label>邮箱：</label>
                          <span>{{ selectedCandidate.resume.personalInfo.email }}</span>
                        </div>
                      </div>
                      <div class="info-row">
                        <div class="info-item">
                          <label>地址：</label>
                          <span>{{ selectedCandidate.resume.personalInfo.location }}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 工作经验 -->
                  <div class="resume-section">
                    <h3 class="section-title">工作经验</h3>
                    <div class="experience-list">
                      <div 
                        v-for="(exp, index) in selectedCandidate.resume.workExperience" 
                        :key="index"
                        class="experience-item"
                      >
                        <div class="exp-header">
                          <h4>{{ exp.position }}</h4>
                          <span class="duration">{{ exp.duration }}</span>
                        </div>
                        <p class="company">{{ exp.company }}</p>
                        <p class="description">{{ exp.description }}</p>
                      </div>
                    </div>
                  </div>

                  <!-- 教育背景 -->
                  <div class="resume-section">
                    <h3 class="section-title">教育背景</h3>
                    <div class="education-list">
                      <div 
                        v-for="(edu, index) in selectedCandidate.resume.education" 
                        :key="index"
                        class="education-item"
                      >
                        <div class="edu-header">
                          <h4>{{ edu.school }}</h4>
                          <span class="duration">{{ edu.duration }}</span>
                        </div>
                        <p class="major">{{ edu.major }} - {{ edu.degree }}</p>
                      </div>
                    </div>
                  </div>

                  <!-- 技能特长 -->
                  <div class="resume-section">
                    <h3 class="section-title">技能特长</h3>
                    <div class="skills-list">
                      <el-tag 
                        v-for="skill in selectedCandidate.resume.skills" 
                        :key="skill"
                        class="skill-tag"
                        type="primary"
                      >
                        {{ skill }}
                      </el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <!-- 面试方案预览Tab -->
            <el-tab-pane label="面试方案" name="interview-plan">
              <div class="interview-plan-preview">
                <div v-if="!selectedCandidate" class="empty-state">
                  <el-empty description="请选择一个候选人并生成面试方案" />
                </div>
                <div v-else-if="!interviewPlan" class="empty-state">
                    <el-empty description="暂无面试方案，请点击生成面试方案按钮" />
                  </div>
                <div v-else class="interview-plan-content">
                  <!-- 方案头部 -->
                  <div class="plan-header">
                    <div class="header-info">
                      <h2>{{ interviewPlan.candidateName }} - 面试方案</h2>
                      <p class="position">{{ interviewPlan.position }}</p>
                      <p class="generated-time">生成时间：{{ interviewPlan.generatedAt }}</p>
                    </div>
                    <el-tag type="success" size="large">AI自动生成</el-tag>
                  </div>

                  <!-- 面试概览 -->
                  <div class="plan-section">
                    <h3 class="section-title">面试概览</h3>
                    <div class="overview-grid">
                      <div class="overview-item">
                        <label>总时长：</label>
                        <span>{{ interviewPlan.overview.totalTime }}</span>
                      </div>
                      <div class="overview-item">
                        <label>难度等级：</label>
                        <span>{{ interviewPlan.overview.difficulty }}</span>
                      </div>
                      <div class="overview-item full-width">
                        <label>重点评估领域：</label>
                        <div class="focus-areas">
                          <el-tag 
                            v-for="area in interviewPlan.overview.focusAreas" 
                            :key="area"
                            class="area-tag"
                            type="info"
                          >
                            {{ area }}
                          </el-tag>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 面试环节 -->
                  <div class="plan-section">
                    <h3 class="section-title">面试环节</h3>
                    <div class="sections-list">
                      <div 
                        v-for="(section, index) in interviewPlan.sections" 
                        :key="index"
                        class="section-item"
                      >
                        <div class="section-header">
                          <h4>{{ section.title }}</h4>
                          <span class="duration">{{ section.duration }}</span>
                        </div>
                        <div class="questions-list">
                          <div 
                            v-for="(question, qIndex) in section.questions" 
                            :key="qIndex"
                            class="question-item"
                          >
                            <span class="question-number">{{ qIndex + 1 }}.</span>
                            <span class="question-text">{{ question }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 评估标准 -->
                  <div class="plan-section">
                    <h3 class="section-title">评估标准</h3>
                    <div class="criteria-list">
                      <div 
                        v-for="(criteria, index) in interviewPlan.evaluationCriteria" 
                        :key="index"
                        class="criteria-item"
                      >
                        <div class="criteria-header">
                          <h4>{{ criteria.category }}</h4>
                          <el-tag type="warning" size="small">{{ criteria.weight }}</el-tag>
                        </div>
                        <p class="criteria-description">{{ criteria.description }}</p>
                      </div>
                    </div>
                  </div>

                  <!-- 面试建议 -->
                  <div class="plan-section">
                    <h3 class="section-title">面试建议</h3>
                    <div class="tips-list">
                      <div 
                        v-for="(tip, index) in interviewPlan.tips" 
                        :key="index"
                        class="tip-item"
                      >
                        <el-icon class="tip-icon"><InfoFilled /></el-icon>
                        <span>{{ tip }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- 操作按钮 -->
                  <div class="plan-actions">
                    <el-button type="primary" @click="startInterview">
                      <el-icon><VideoCamera /></el-icon>
                      开始面试
                    </el-button>
                    <el-button @click="exportPlan">
                      <el-icon><Download /></el-icon>
                      导出方案
                    </el-button>
                    <el-button @click="regeneratePlan" :loading="generatingPlan">
                      <el-icon><Refresh /></el-icon>
                      重新生成
                    </el-button>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </div>
    </div>

    <!-- 创建面试对话框 -->
    <el-dialog 
      v-model="showCreateDialog" 
      title="创建面试" 
      width="600px"
    >
      <el-form 
        ref="createFormRef" 
        :model="createForm" 
        :rules="createRules" 
        label-width="100px"
      >
        <el-form-item label="候选人" prop="candidateName">
          <el-input v-model="createForm.candidateName" placeholder="请输入候选人姓名" />
        </el-form-item>
        
        <el-form-item label="面试职位" prop="position">
          <el-input v-model="createForm.position" placeholder="请输入面试职位" />
        </el-form-item>
        
        <el-form-item label="面试日期" prop="date">
          <el-date-picker
            v-model="createForm.date"
            type="date"
            placeholder="选择面试日期"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="面试时间" prop="time">
          <el-time-picker
            v-model="createForm.time"
            placeholder="选择面试时间"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="面试官" prop="interviewer">
          <el-input v-model="createForm.interviewer" placeholder="请输入面试官姓名" />
        </el-form-item>
        
        <el-form-item label="面试类型" prop="type">
          <el-radio-group v-model="createForm.type">
            <el-radio label="技术面试">技术面试</el-radio>
            <el-radio label="HR面试">HR面试</el-radio>
            <el-radio label="综合面试">综合面试</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input 
            v-model="createForm.notes" 
            type="textarea" 
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createInterview">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'

// 响应式数据
const activeTab = ref('resume')
const selectedCandidate = ref(null)
const generatingPlan = ref(false)
const interviewPlan = ref(null)

// 筛选相关数据
const filters = reactive({
  name: '',
  position: ''
})

// 候选人数据
const candidates = ref([
  {
    id: 1,
    name: '张三',
    position: '前端开发工程师',
    experience: 3,
    education: '本科',
    location: '北京',
    totalScore: 85,
    scores: {
      skillMatch: 4,
      experience: 4,
      education: 4,
      overall: 4
    },
    resume: {
      personalInfo: {
        name: '张三',
        age: 28,
        phone: '138****1234',
        email: 'zhangsan@example.com',
        location: '北京市朝阳区'
      },
      workExperience: [
        {
          company: 'ABC科技有限公司',
          position: '前端开发工程师',
          duration: '2021.03 - 至今',
          description: '负责公司主要产品的前端开发工作，使用React、Vue等技术栈'
        }
      ],
      education: [
        {
          school: '北京理工大学',
          major: '计算机科学与技术',
          degree: '本科',
          duration: '2017.09 - 2021.06'
        }
      ],
      skills: ['JavaScript', 'React', 'Vue', 'TypeScript', 'Node.js']
    }
  },
  {
    id: 2,
    name: '李四',
    position: 'React开发工程师',
    experience: 5,
    education: '硕士',
    location: '上海',
    totalScore: 92,
    scores: {
      skillMatch: 5,
      experience: 5,
      education: 4,
      overall: 5
    },
    resume: {
      personalInfo: {
        name: '李四',
        age: 30,
        phone: '139****5678',
        email: 'lisi@example.com',
        location: '上海市浦东新区'
      },
      workExperience: [
        {
          company: 'XYZ互联网公司',
          position: '高级前端开发工程师',
          duration: '2019.06 - 至今',
          description: '负责大型React项目的架构设计和开发，团队技术负责人'
        }
      ],
      education: [
        {
          school: '复旦大学',
          major: '软件工程',
          degree: '硕士',
          duration: '2017.09 - 2019.06'
        }
      ],
      skills: ['React', 'TypeScript', 'Redux', 'Webpack', 'Docker']
    }
  },
  {
    id: 3,
    name: '王五',
    position: 'Vue开发工程师',
    experience: 2,
    education: '本科',
    location: '深圳',
    totalScore: 78,
    scores: {
      skillMatch: 4,
      experience: 3,
      education: 4,
      overall: 4
    },
    resume: {
      personalInfo: {
        name: '王五',
        age: 25,
        phone: '137****9012',
        email: 'wangwu@example.com',
        location: '深圳市南山区'
      },
      workExperience: [
        {
          company: 'DEF创业公司',
          position: 'Vue开发工程师',
          duration: '2022.07 - 至今',
          description: '负责公司产品的前端开发，主要使用Vue3和TypeScript'
        }
      ],
      education: [
        {
          school: '深圳大学',
          major: '信息管理与信息系统',
          degree: '本科',
          duration: '2018.09 - 2022.06'
        }
      ],
      skills: ['Vue', 'JavaScript', 'TypeScript', 'Element Plus', 'Vite']
    }
  }
])

// 计算属性
const availablePositions = computed(() => {
  const positions = [...new Set(candidates.value.map(c => c.position))]
  return positions.sort()
})

const filteredCandidates = computed(() => {
  return candidates.value.filter(candidate => {
    const nameMatch = !filters.name || 
      candidate.name.toLowerCase().includes(filters.name.toLowerCase())
    
    const positionMatch = !filters.position || 
      candidate.position === filters.position
    
    return nameMatch && positionMatch
  })
})

const filteredCandidatesCount = computed(() => filteredCandidates.value.length)
const totalCandidatesCount = computed(() => candidates.value.length)

// 方法
const getScoreType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 80) return 'warning'
  if (score >= 70) return 'info'
  return 'danger'
}

const getScoreColor = (score) => {
  if (score >= 90) return '#67c23a'
  if (score >= 80) return '#e6a23c'
  if (score >= 70) return '#409eff'
  return '#f56c6c'
}

const selectCandidate = (candidate) => {
  selectedCandidate.value = candidate
  activeTab.value = 'resume'
  // 清除之前的面试方案
  interviewPlan.value = null
  ElMessage.success(`已选择候选人：${candidate.name}`)
}

const refreshCandidates = () => {
  ElMessage.success('候选人列表已刷新')
  // 这里可以调用API刷新数据
}

const viewResume = (candidate) => {
  selectCandidate(candidate)
  activeTab.value = 'resume'
}

const generateInterviewPlan = async (candidate) => {
  try {
    selectedCandidate.value = candidate
    generatingPlan.value = true
    activeTab.value = 'interview-plan'
    
    ElMessage.info('正在生成面试方案，请稍候...')
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 模拟生成的面试方案
    interviewPlan.value = {
      candidateId: candidate.id,
      candidateName: candidate.name,
      position: candidate.position,
      generatedAt: new Date().toLocaleString(),
      overview: {
        totalTime: '60分钟',
        difficulty: '中等',
        focusAreas: ['技术能力', '项目经验', '团队协作', '学习能力']
      },
      sections: [
        {
          title: '开场介绍',
          duration: '5分钟',
          questions: [
            '请简单介绍一下自己',
            '为什么选择我们公司？'
          ]
        },
        {
          title: '技术能力评估',
          duration: '30分钟',
          questions: [
            `请介绍一下你在${candidate.position}方面的经验`,
            '描述一个你最有挑战性的项目',
            '如何处理项目中的技术难题？',
            '对于新技术的学习方法是什么？'
          ]
        },
        {
          title: '项目经验深入',
          duration: '20分钟',
          questions: [
            '请详细介绍你最近的一个项目',
            '在团队协作中遇到过什么困难？',
            '如何保证代码质量？',
            '对项目架构有什么思考？'
          ]
        },
        {
          title: '综合素质评估',
          duration: '5分钟',
          questions: [
            '你的职业规划是什么？',
            '还有什么问题想了解的吗？'
          ]
        }
      ],
      evaluationCriteria: [
        {
          category: '技术能力',
          weight: '40%',
          description: '评估候选人的技术深度和广度'
        },
        {
          category: '项目经验',
          weight: '30%',
          description: '评估候选人的实际项目经验和解决问题能力'
        },
        {
          category: '沟通表达',
          weight: '20%',
          description: '评估候选人的沟通能力和表达清晰度'
        },
        {
          category: '学习能力',
          weight: '10%',
          description: '评估候选人的学习意愿和适应能力'
        }
      ],
      tips: [
        '注意观察候选人的思考过程',
        '鼓励候选人提出问题',
        '关注候选人的团队协作意识',
        '评估候选人的抗压能力'
      ]
    }
    
    ElMessage.success('面试方案生成完成！')
  } catch (error) {
    console.error('生成面试方案失败:', error)
    ElMessage.error('生成面试方案失败，请重试')
  } finally {
    generatingPlan.value = false
  }
}

const startInterview = () => {
  if (!selectedCandidate.value || !interviewPlan.value) {
    ElMessage.warning('请先选择候选人并生成面试方案')
    return
  }
  ElMessage.success(`开始面试：${selectedCandidate.value.name}`)
  // 这里可以跳转到面试界面或打开面试窗口
}

const exportPlan = () => {
  if (!interviewPlan.value) {
    ElMessage.warning('暂无面试方案可导出')
    return
  }
  ElMessage.success('面试方案导出成功')
  // 这里可以实现导出功能
}

const regeneratePlan = () => {
  if (!selectedCandidate.value) {
    ElMessage.warning('请先选择候选人')
    return
  }
  generateInterviewPlan(selectedCandidate.value)
}

// 筛选相关方法
const handleFilterChange = () => {
  // 筛选变化时的处理逻辑
  if (selectedCandidate.value && !filteredCandidates.value.find(c => c.id === selectedCandidate.value.id)) {
    // 如果当前选中的候选人被筛选掉了，清除选择
    selectedCandidate.value = null
    interviewPlan.value = null
    activeTab.value = 'resume'
  }
}

const clearFilters = () => {
  filters.name = ''
  filters.position = ''
  ElMessage.success('筛选条件已重置')
}
</script>

<style lang="scss" scoped>
.smart-interview {
  height: 100%;
  overflow-y: auto;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 20px;
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 24px;
    
    .header-left {
      flex: 1;
    }
    
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
    
    .filter-section {
      flex-shrink: 0;
      
      .filter-row {
        display: flex;
        align-items: flex-end;
        gap: 16px;
        flex-wrap: wrap;
      }
      
      .filter-item {
        display: flex;
        flex-direction: column;
        gap: 6px;
        
        .filter-label {
          font-size: 14px;
          font-weight: 500;
          color: #374151;
          margin: 0;
        }
      }
      
      .filter-actions {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .el-button {
          background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
          border: 1px solid #d1d5db;
          color: #374151;
          border-radius: 8px;
          font-weight: 500;
          transition: all 0.3s ease;
          
          &:hover {
            background: linear-gradient(135deg, #e5e7eb, #d1d5db);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          }
        }
        
        .el-tag {
          font-weight: 500;
        }
      }
    }
  }
  
  .header-actions {
    .el-button {
      background: linear-gradient(135deg, #667eea, #764ba2);
      border: none;
      color: white;
      padding: 12px 24px;
      border-radius: 12px;
      font-weight: 600;
      transition: all 0.3s ease;
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
      }
    }
  }
}

.main-content {
  display: flex;
  gap: 20px;
  height: calc(100vh - 200px);
}

.left-panel {
  width: 450px;
  flex-shrink: 0;
}

.right-panel {
  flex: 1;
  min-width: 0;
}

.candidate-list-card {
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
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
    color: #1e293b;
  }
}

.candidate-list {
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

.candidate-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fff;
  
  &:hover {
    border-color: #409eff;
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  }
  
  &.active {
    border-color: #409eff;
    background: #f0f9ff;
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
  }
}

.candidate-info {
  margin-bottom: 12px;
}

.candidate-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.candidate-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.candidate-position {
  margin: 0 0 8px 0;
  color: #606266;
  font-size: 14px;
}

.candidate-details {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.detail-item {
  font-size: 12px;
  color: #909399;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
}

.score-items {
  margin-bottom: 12px;
}

.score-row {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.score-item {
  flex: 1;
  
  .score-label {
    display: block;
    font-size: 12px;
    color: #909399;
    margin-bottom: 4px;
  }
}

.candidate-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.empty-candidates {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  
  :deep(.el-empty) {
    .el-empty__description {
      color: #64748b;
      font-size: 14px;
    }
    
    .el-button {
      background: linear-gradient(135deg, #667eea, #764ba2);
      border: none;
      color: white;
      border-radius: 8px;
      font-weight: 500;
      
      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
      }
    }
  }
}

.content-card {
  height: 100%;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  
  :deep(.el-card__body) {
    height: calc(100% - 60px);
    padding: 0;
  }
}

.content-tabs {
  height: 100%;
  
  :deep(.el-tabs__header) {
    margin: 0;
    padding: 0 20px;
    background: linear-gradient(135deg, #f8fafc, #e2e8f0);
    border-radius: 16px 16px 0 0;
  }
  
  :deep(.el-tabs__content) {
    height: calc(100% - 60px);
    padding: 20px;
  }
  
  :deep(.el-tab-pane) {
    height: 100%;
  }
}

.resume-preview {
  height: 100%;
  overflow-y: auto;
  
  .empty-state {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
  }
  
  .resume-content {
    .resume-section {
      margin-bottom: 24px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .section-title {
        font-size: 18px;
        font-weight: 600;
        color: #1e293b;
        margin: 0 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #e2e8f0;
      }
    }
    
    .personal-info {
      .info-row {
        display: flex;
        gap: 24px;
        margin-bottom: 12px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .info-item {
          flex: 1;
          
          label {
            font-weight: 600;
            color: #64748b;
            margin-right: 8px;
          }
          
          span {
            color: #1e293b;
          }
        }
      }
    }
    
    .experience-list {
      .experience-item {
        padding: 16px;
        background: #f8fafc;
        border-radius: 8px;
        margin-bottom: 12px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .exp-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
          
          h4 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
          }
          
          .duration {
            font-size: 14px;
            color: #64748b;
            background: #e2e8f0;
            padding: 4px 8px;
            border-radius: 4px;
          }
        }
        
        .company {
          margin: 0 0 8px 0;
          font-weight: 500;
          color: #475569;
        }
        
        .description {
          margin: 0;
          color: #64748b;
          line-height: 1.5;
        }
      }
    }
    
    .education-list {
      .education-item {
        padding: 16px;
        background: #f8fafc;
        border-radius: 8px;
        margin-bottom: 12px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .edu-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
          
          h4 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
          }
          
          .duration {
            font-size: 14px;
            color: #64748b;
            background: #e2e8f0;
            padding: 4px 8px;
            border-radius: 4px;
          }
        }
        
        .major {
          margin: 0;
          color: #475569;
          font-weight: 500;
        }
      }
    }
    
    .skills-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      
      .skill-tag {
        margin: 0;
      }
    }
  }
}

.interview-plan-preview {
  height: 100%;
  overflow-y: auto;
  
  .empty-state {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
  }
  
  .interview-plan-content {
    .plan-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 24px;
      padding: 20px;
      background: linear-gradient(135deg, #f8fafc, #e2e8f0);
      border-radius: 8px;
      
      .header-info {
        h2 {
          margin: 0 0 8px 0;
          font-size: 20px;
          font-weight: 600;
          color: #1e293b;
        }
        
        .position {
          margin: 0 0 4px 0;
          color: #475569;
          font-weight: 500;
        }
        
        .generated-time {
          margin: 0;
          font-size: 14px;
          color: #64748b;
        }
      }
    }
    
    .plan-section {
      margin-bottom: 24px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .section-title {
        font-size: 18px;
        font-weight: 600;
        color: #1e293b;
        margin: 0 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #e2e8f0;
      }
    }
    
    .overview-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      
      .overview-item {
        &.full-width {
          grid-column: 1 / -1;
        }
        
        label {
          font-weight: 600;
          color: #64748b;
          margin-right: 8px;
        }
        
        span {
          color: #1e293b;
        }
        
        .focus-areas {
          margin-top: 8px;
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          
          .area-tag {
            margin: 0;
          }
        }
      }
    }
    
    .sections-list {
      .section-item {
        padding: 16px;
        background: #f8fafc;
        border-radius: 8px;
        margin-bottom: 12px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          
          h4 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
          }
          
          .duration {
            font-size: 14px;
            color: #64748b;
            background: #e2e8f0;
            padding: 4px 8px;
            border-radius: 4px;
          }
        }
        
        .questions-list {
          .question-item {
            display: flex;
            gap: 8px;
            margin-bottom: 8px;
            
            &:last-child {
              margin-bottom: 0;
            }
            
            .question-number {
              font-weight: 600;
              color: #667eea;
              flex-shrink: 0;
            }
            
            .question-text {
              color: #475569;
              line-height: 1.5;
            }
          }
        }
      }
    }
    
    .criteria-list {
      .criteria-item {
        padding: 16px;
        background: #f8fafc;
        border-radius: 8px;
        margin-bottom: 12px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .criteria-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
          
          h4 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
          }
        }
        
        .criteria-description {
          margin: 0;
          color: #64748b;
          line-height: 1.5;
        }
      }
    }
    
    .tips-list {
      .tip-item {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        margin-bottom: 12px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .tip-icon {
          color: #667eea;
          margin-top: 2px;
          flex-shrink: 0;
        }
        
        span {
          color: #475569;
          line-height: 1.5;
        }
      }
    }
    
    .plan-actions {
      margin-top: 24px;
      padding-top: 20px;
      border-top: 1px solid #e2e8f0;
      display: flex;
      gap: 12px;
      justify-content: center;
      
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
}

.interview-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.interview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(248, 250, 252, 0.9));
  border: 1px solid rgba(226, 232, 240, 0.5);
  border-radius: 12px;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(102, 126, 234, 0.15);
    border-color: rgba(102, 126, 234, 0.3);
  }
  
  .interview-info {
    flex: 1;
    
    .candidate-info {
      margin-bottom: 12px;
      
      h3 {
        font-size: 18px;
        font-weight: 600;
        background: linear-gradient(135deg, #1e293b, #475569);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 4px 0;
      }
      
      p {
        color: #64748b;
        margin: 0;
        font-weight: 500;
      }
    }
    
    .interview-details {
      display: flex;
      gap: 24px;
      
      .detail-item {
        display: flex;
        align-items: center;
        gap: 6px;
        color: #64748b;
        font-size: 14px;
        font-weight: 500;
        
        .el-icon {
          font-size: 16px;
          color: #667eea;
        }
      }
    }
  }
  
  .interview-actions {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 12px;
    
    .status-tag {
      margin: 0;
      font-weight: 600;
      border-radius: 8px;
      
      &.el-tag--warning {
        background: linear-gradient(135deg, #fbbf24, #f59e0b);
        color: white;
        border: none;
      }
      
      &.el-tag--success {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        border: none;
      }
    }
    
    .action-buttons {
      display: flex;
      gap: 8px;
      
      .el-button {
        border-radius: 8px;
        font-weight: 500;
        
        &.el-button--primary {
          background: linear-gradient(135deg, #667eea, #764ba2);
          border: none;
          
          &:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
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
          }
        }
      }
    }
  }
}

// 对话框样式优化
:deep(.el-dialog) {
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  
  .el-dialog__header {
    background: linear-gradient(135deg, #f8fafc, #e2e8f0);
    border-radius: 16px 16px 0 0;
    padding: 20px 24px;
    
    .el-dialog__title {
      font-weight: 600;
      color: #1e293b;
    }
  }
  
  .el-dialog__body {
    padding: 24px;
  }
  
  .el-dialog__footer {
    padding: 20px 24px;
    background: rgba(248, 250, 252, 0.5);
    border-radius: 0 0 16px 16px;
    
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
  .el-form-item__label {
    color: #374151;
    font-weight: 600;
  }
  
  .el-input__wrapper {
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    
    &:hover {
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
  }
  
  .el-radio {
    .el-radio__label {
      color: #374151;
      font-weight: 500;
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

// 响应式设计
@media (max-width: 768px) {
  .smart-interview {
    padding: 12px;
  }
  
  .page-header {
    padding: 20px;
    
    .header-content {
      flex-direction: column;
      gap: 20px;
      
      .filter-section {
        .filter-row {
          flex-direction: column;
          gap: 12px;
          align-items: stretch;
        }
        
        .filter-item {
          .el-input,
          .el-select {
            width: 100% !important;
          }
        }
        
        .filter-actions {
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 8px;
          
          .el-button {
            flex: 1;
            min-width: 120px;
          }
        }
      }
    }
    
    .header-actions {
      width: 100%;
      display: flex;
      justify-content: center;
    }
  }
  
  .main-content {
    flex-direction: column;
    height: auto;
    gap: 16px;
  }
  
  .left-panel {
    width: 100%;
  }
  
  .candidate-list {
    max-height: 400px;
  }
  
  .candidate-item {
    .candidate-details {
      flex-direction: column;
      gap: 8px;
    }
    
    .score-row {
      flex-direction: column;
      gap: 8px;
    }
    
    .candidate-actions {
      flex-direction: column;
      gap: 8px;
      
      .el-button {
        width: 100%;
      }
    }
  }
  
  .overview-grid {
    grid-template-columns: 1fr !important;
  }
  
  .plan-actions {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
}
</style>