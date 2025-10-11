<template>
  <div class="resume-screening">
    <div class="page-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><User /></el-icon>
            简历筛选
          </h1>
          <p class="page-description">智能简历筛选与评估，快速找到合适的候选人</p>
        </div>
        <div class="header-actions">
          <el-button @click="openUploadDialog" type="primary" size="large">
            <el-icon><Upload /></el-icon>
            上传简历
          </el-button>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <div class="main-content">
        <!-- 左侧简历列表 -->
        <div class="resume-list-panel">
          <el-card class="list-card">
            <template #header>
              <div class="list-header">
                <span class="list-title">
                  <el-icon><List /></el-icon>
                  简历列表 ({{ pagination.total }})
                </span>
                <div class="list-actions">
                  <el-input
                    v-model="filters.keyword"
                    placeholder="搜索简历..."
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

            <!-- 筛选器 -->
            <div class="filters-section">
              <div class="filter-group">
                <el-select
                  v-model="filters.experience"
                  placeholder="工作经验"
                  clearable
                  size="small"
                  style="width: 120px"
                  @change="applyFilters"
                >
                  <el-option label="不限" value="" />
                  <el-option label="应届生" value="0-1年" />
                  <el-option label="1-3年" value="1-3年" />
                  <el-option label="3-5年" value="3-5年" />
                  <el-option label="5-10年" value="5-10年" />
                  <el-option label="10年以上" value="10年以上" />
                </el-select>
              </div>
              
              <div class="filter-group">
                <el-select
                  v-model="filters.education"
                  placeholder="学历"
                  clearable
                  size="small"
                  style="width: 100px"
                  @change="applyFilters"
                >
                  <el-option label="不限" value="" />
                  <el-option label="专科" value="专科" />
                  <el-option label="本科" value="本科" />
                  <el-option label="硕士" value="硕士" />
                  <el-option label="博士" value="博士" />
                </el-select>
              </div>

              <div class="filter-group">
                <el-button @click="resetFilters" size="small">
                  <el-icon><Refresh /></el-icon>
                  重置
                </el-button>
              </div>
            </div>

            <!-- 简历列表内容 -->
            <div class="resume-list-content">
              <div v-if="loading" class="loading-container">
                <el-skeleton :rows="5" animated />
              </div>
              
              <div v-else-if="filteredResumeList.length === 0" class="empty-container">
                <el-empty description="暂无简历数据" :image-size="120">
                  <el-button type="primary" @click="openUploadDialog">
                    <el-icon><Upload /></el-icon>
                    上传第一份简历
                  </el-button>
                </el-empty>
              </div>

              <div v-else class="resume-items">
                <div
                  v-for="resume in filteredResumeList"
                  :key="resume.id"
                  :class="['resume-item', { active: selectedResume?.id === resume.id }]"
                  @click="selectResume(resume)"
                >
                  <div class="resume-item-header">
                    <div class="candidate-info">
                      <h4 class="candidate-name">{{ resume.name }}</h4>
                      <div class="score-badge">
                        <el-tag :type="getScoreType(resume.matchScore)" size="small">
                          {{ resume.matchScore }}分
                        </el-tag>
                      </div>
                    </div>
                  </div>
                  
                  <div class="resume-item-content">
                    <div class="position-info">
                      <span class="position-text">{{ resume.currentPosition || '未填写职位' }}</span>
                    </div>
                    
                    <div class="resume-actions">
                      <el-button @click.stop="viewResumeDetail(resume)" type="primary" size="small">
                        <el-icon><View /></el-icon>
                        简历预览
                      </el-button>
                      <el-button @click.stop="deleteResume(resume)" type="danger" size="small">
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 分页 -->
              <div v-if="filteredResumeList.length > 0" class="pagination-container">
                <el-pagination
                  v-model:current-page="pagination.page"
                  v-model:page-size="pagination.size"
                  :total="pagination.total"
                  :page-sizes="[10, 20, 50]"
                  layout="total, sizes, prev, pager, next"
                  small
                  @size-change="handleSizeChange"
                  @current-change="handlePageChange"
                />
              </div>
            </div>
          </el-card>
        </div>

        <!-- 右侧详情区域 -->
        <div class="resume-detail-panel">
          <!-- 欢迎页面 -->
          <div v-if="!selectedResume" class="welcome-container">
            <el-card class="welcome-card">
              <div class="welcome-content">
                <div class="welcome-icon">
                  <el-icon size="80"><User /></el-icon>
                </div>
                <h2>选择简历查看详情</h2>
                <p>点击左侧的简历项目查看详细信息和评价结果</p>
                <div class="welcome-actions">
                  <el-button type="primary" @click="openUploadDialog" size="large">
                    <el-icon><Upload /></el-icon>
                    上传新简历
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>

          <!-- 简历详情内容 -->
          <div v-else class="resume-detail-content">
            <!-- 详情头部 -->
            <div class="detail-header">
              <div class="candidate-profile">
                <el-avatar :size="60" :src="selectedResume.avatar">
                  {{ selectedResume.name?.charAt(0) }}
                </el-avatar>
                <div class="profile-info">
                  <h3>{{ selectedResume.name }}</h3>
                  <p class="current-position">{{ selectedResume.currentPosition }}</p>
                  <div class="profile-meta">
                    <span class="meta-item">{{ selectedResume.experience }}</span>
                    <span class="meta-divider">|</span>
                    <span class="meta-item">{{ selectedResume.education }}</span>
                    <span class="meta-divider">|</span>
                    <span class="meta-item">{{ selectedResume.age }}岁</span>
                  </div>
                  <!-- 操作按钮行 -->
                  <div class="action-buttons">
                    <el-button type="danger" size="default" @click="handleReject">
                      <el-icon><Close /></el-icon>
                      不通过
                    </el-button>
                    <el-button type="primary" size="default" @click="handleInterview">
                      <el-icon><Check /></el-icon>
                      面试
                    </el-button>
                  </div>
                </div>
              </div>
              <div class="score-section">
                <div class="score-display">
                  <el-progress
                    type="circle"
                    :percentage="selectedResume.matchScore"
                    :color="getScoreColor(selectedResume.matchScore)"
                    :width="80"
                  >
                    <template #default="{ percentage }">
                      <span class="score-text">{{ percentage }}分</span>
                    </template>
                  </el-progress>
                </div>
                <p class="score-label">匹配度</p>
              </div>
            </div>

            <!-- 详情主要内容 - 两列布局 -->
            <div class="detail-main">
              <div class="two-column-layout">
                <!-- 左列：简历详情 -->
                <div class="left-column">
                  <div class="column-header">
                    <h4 class="column-title">
                      <el-icon><Document /></el-icon>
                      简历详情
                    </h4>
                  </div>
                  <div class="column-content">
                    <div class="resume-content-section">
                      <div class="content-display" v-html="formattedResumeContent"></div>
                    </div>
                  </div>
                </div>

                <!-- 右列：评价结果 -->
                <div class="right-column">
                  <div class="column-header">
                    <h4 class="column-title">
                      <el-icon><Star /></el-icon>
                      评价结果
                    </h4>
                  </div>
                  <div class="column-content">
                    <div class="evaluation-section">
                      <div v-if="selectedResume.evaluationMetrics && selectedResume.evaluationMetrics.length > 0" class="evaluation-content">
                        <div
                          v-for="metric in selectedResume.evaluationMetrics"
                          :key="metric.name"
                          class="evaluation-item"
                        >
                          <div class="metric-header">
                            <h4 class="metric-name">{{ metric.name }}</h4>
                            <div class="metric-score">
                              <el-tag :type="getMetricScoreType(metric.score, metric.max)">
                                {{ metric.score }}/{{ metric.max }}分
                              </el-tag>
                            </div>
                          </div>
                          <div class="metric-reason">
                            <p>{{ metric.reason }}</p>
                          </div>
                        </div>
                      </div>
                      <div v-else class="no-evaluation">
                        <el-empty description="暂无评价数据" :image-size="100" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传简历对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传简历"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="upload-section">
        <!-- JD选择器 -->
        <div class="jd-selector-section">
          <el-form-item label="选择对应JD" required>
            <el-select
              v-model="selectedJDId"
              placeholder="请选择要匹配的职位描述"
              style="width: 100%"
              filterable
              :loading="jdListLoading"
            >
              <el-option
                v-for="jd in jdList"
                :key="jd.id"
                :label="`${jd.title} - ${jd.department || '未知部门'}`"
                :value="jd.id"
              >
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span>{{ jd.title }}</span>
                  <span style="color: #8492a6; font-size: 13px;">{{ jd.department || '未知部门' }}</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
        </div>
        
        <el-upload
          ref="uploadRef"
          class="upload-dragger"
          drag
          :action="uploadUrl"
          :headers="uploadHeaders"
          :data="uploadData"
          :before-upload="beforeUpload"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :file-list="fileList"
          accept=".pdf,.doc,.docx"
          :limit="1"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 PDF、DOC、DOCX 格式，文件大小不超过 10MB
            </div>
          </template>
        </el-upload>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showUploadDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmUpload" :loading="uploading">
            确定上传
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Star, Close, Check } from '@element-plus/icons-vue'
import { resumeApi } from '@/api/resume'
import { jdApi } from '@/api/jd'
import { marked } from 'marked'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

// 用户存储
const authStore = useAuthStore()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const showUploadDialog = ref(false)
const uploading = ref(false)
const selectedResume = ref(null)
const activeTab = ref('content')

// 简历列表数据
const resumeList = ref([])
const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

// 筛选条件
const filters = reactive({
  keyword: '',
  experience: '',
  education: '',
  scoreRange: [0, 100]
})

// 上传相关
const fileList = ref([])
const uploadUrl = ref('/api/v1/resume-evaluation/evaluate')
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${authStore.token}`
}))
const uploadData = ref({})

// JD相关数据
const jdList = ref([])
const jdListLoading = ref(false)
const selectedJDId = ref('')

// 计算属性
const filteredResumeList = computed(() => {
  let filtered = resumeList.value

  // 关键词搜索
  if (filters.keyword) {
    const keyword = filters.keyword.toLowerCase()
    filtered = filtered.filter(resume => 
      resume.name?.toLowerCase().includes(keyword) ||
      resume.currentPosition?.toLowerCase().includes(keyword) ||
      resume.school?.toLowerCase().includes(keyword) ||
      resume.skills?.some(skill => skill.toLowerCase().includes(keyword))
    )
  }

  // 工作经验筛选
  if (filters.experience) {
    filtered = filtered.filter(resume => resume.experience === filters.experience)
  }

  // 学历筛选
  if (filters.education) {
    filtered = filtered.filter(resume => resume.education === filters.education)
  }

  // 评分范围筛选
  filtered = filtered.filter(resume => 
    resume.matchScore >= filters.scoreRange[0] && 
    resume.matchScore <= filters.scoreRange[1]
  )

  return filtered
})

const formattedResumeContent = computed(() => {
  if (!selectedResume.value?.resumeContent) return ''
  return marked(selectedResume.value.resumeContent)
})

// 方法
const fetchResumeList = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    
    console.log('获取简历列表，参数:', params)
    const response = await resumeApi.getResumeHistory(params)
    console.log('完整的API响应:', response)
    console.log('后端返回的简历数据:', response)
    
    if (response && Array.isArray(response.items)) {
      // 映射后端数据到前端格式
      resumeList.value = response.items.map(item => ({
        id: item.id,
        name: item.candidate_name,
        currentPosition: item.candidate_position,
        experience: item.work_years,
        education: item.education_level,
        age: item.candidate_age,
        gender: item.candidate_gender,
        school: item.school,
        matchScore: item.total_score,
        skills: item.skills || [],
        highlights: item.highlights || [],
        resumeContent: item.resume_content,
        originalFilename: item.original_filename,
        fileType: item.file_type,
        evaluationMetrics: item.evaluation_metrics || [],
        createdAt: item.created_at
      }))
      
      console.log('映射后的简历列表:', resumeList.value)
      
      // 按创建时间降序排列
      resumeList.value.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
      console.log('排序后的简历列表:', resumeList.value)
      
      pagination.total = response.total || resumeList.value.length
    } else {
      resumeList.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('获取简历列表失败:', error)
    ElMessage.error('获取简历列表失败')
    resumeList.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

// 获取JD列表
const fetchJDList = async () => {
  try {
    jdListLoading.value = true
    const response = await jdApi.getJDList({
      page: 1,
      size: 100, // 获取所有可用的JD
      // status_filter: 'published' // 只获取已发布的JD
    })
    
    if (response && Array.isArray(response.items)) {
      jdList.value = response.items
    } else {
      jdList.value = []
    }
  } catch (error) {
    console.error('获取JD列表失败:', error)
    ElMessage.error('获取JD列表失败')
    jdList.value = []
  } finally {
    jdListLoading.value = false
  }
}

const selectResume = (resume) => {
  selectedResume.value = resume
  activeTab.value = 'content'
}

const viewResumeDetail = (resume) => {
  selectResume(resume)
}

const deleteResume = async (resume) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${resume.name} 的简历吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await resumeApi.deleteResume(resume.id)
    ElMessage.success('删除成功')
    
    // 如果删除的是当前选中的简历，清空选中状态
    if (selectedResume.value?.id === resume.id) {
      selectedResume.value = null
    }
    
    await fetchResumeList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除简历失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleSearch = () => {
  // 搜索逻辑已在计算属性中处理
}

const applyFilters = () => {
  // 筛选逻辑已在计算属性中处理
}

const resetFilters = () => {
  filters.keyword = ''
  filters.experience = ''
  filters.education = ''
  filters.scoreRange = [0, 100]
}

// 操作按钮处理函数
const handleReject = async () => {
  if (!selectedResume.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要将候选人 ${selectedResume.value.name} 标记为不通过吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 调用API更新简历状态
    await resumeApi.updateResumeStatus(selectedResume.value.id, 'rejected')
    ElMessage.success('已标记为不通过')
    
    // 刷新列表
    await fetchResumeList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('操作失败:', error)
      ElMessage.error('操作失败')
    }
  }
}

const handleInterview = async () => {
  if (!selectedResume.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要将候选人 ${selectedResume.value.name} 安排面试吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info',
      }
    )
    
    // 调用API更新简历状态
    await resumeApi.updateResumeStatus(selectedResume.value.id, 'interview')
    ElMessage.success('已安排面试')
    
    // 刷新列表
    await fetchResumeList()
    
    // 跳转到智能面试页面
    await router.push('/recruitment/smart-interview')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('操作失败:', error)
      ElMessage.error('操作失败')
    }
  }
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchResumeList()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchResumeList()
}

// 上传相关方法
const beforeUpload = (file) => {
  // 检查是否选择了JD
  if (!selectedJDId.value) {
    ElMessage.warning('请先选择对应的JD')
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
  
  // 设置上传数据
  uploadData.value = {
    job_description_id: selectedJDId.value
  }
  
  uploading.value = true
  return true
}

const handleUploadSuccess = (response) => {
  uploading.value = false
  showUploadDialog.value = false
  fileList.value = []
  
  // 后端直接返回评价结果数据，检查是否有id字段表示成功
  if (response && response.id) {
    ElMessage.success('简历上传并评价成功')
    fetchResumeList()
  } else {
    ElMessage.error('上传失败：返回数据格式错误')
  }
}

const handleUploadError = (error) => {
  uploading.value = false
  console.error('上传失败:', error)
  ElMessage.error('上传失败，请重试')
}

// 打开上传弹窗
const openUploadDialog = () => {
  selectedJDId.value = ''
  fileList.value = []
  uploadData.value = {}
  showUploadDialog.value = true
}

const confirmUpload = () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }
  // 触发上传
  uploadRef.value.submit()
}

// 工具方法
const getScoreType = (score) => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

const getScoreColor = (score) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

const getMetricScoreType = (score, max) => {
  const percentage = (score / max) * 100
  if (percentage >= 80) return 'success'
  if (percentage >= 60) return 'warning'
  return 'danger'
}

// 生命周期
onMounted(() => {
  fetchResumeList()
  fetchJDList()
})
</script>

<style lang="scss" scoped>
.resume-screening {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
}

.resume-screening::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
  background-size: 20px 20px;
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

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  
  .header-left {
    .page-title {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 28px;
      font-weight: 700;
      background: linear-gradient(135deg, #667eea, #764ba2);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin: 0 0 8px 0;
    }
    
    .page-description {
      color: #606266;
      margin: 0;
      font-size: 14px;
    }
  }
}

.main-content {
  flex: 1;
  display: flex;
  gap: 20px;
  min-height: 0;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.resume-list-panel {
  width: 400px;
  height: 600px;
  flex-shrink: 0;
  
  .list-card {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
    backdrop-filter: blur(25px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    
    :deep(.el-card__body) {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 0;
    }
  }
  
  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .list-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      color: #303133;
    }
  }
  
  .filters-section {
    display: flex;
    gap: 10px;
    padding: 16px;
    border-bottom: 1px solid #ebeef5;
    flex-wrap: wrap;
  }
  
  .resume-list-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    max-height: 500px;
  }
  
  .resume-items {
    flex: 1;
    max-height: 500px;
    overflow-y: scroll;
    padding: 0 16px;
    margin: 0 -16px;
    
    // 自定义滚动条样式
    &::-webkit-scrollbar {
      width: 8px;
    }
    
    &::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.1);
      border-radius: 4px;
    }
    
    &::-webkit-scrollbar-thumb {
      background: rgba(102, 126, 234, 0.6);
      border-radius: 4px;
      
      &:hover {
        background: rgba(102, 126, 234, 0.8);
      }
    }
  }
  
  .resume-item {
    padding: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    cursor: pointer;
    transition: all 0.3s;
    border-radius: 12px;
    margin-bottom: 8px;
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(10px);
    
    &:hover {
      background: rgba(255, 255, 255, 0.9);
      box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
      transform: translateY(-2px);
      border-color: #667eea;
    }
    
    &.active {
      background: rgba(102, 126, 234, 0.1);
      border-left: 3px solid #667eea;
      box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
    }
    
    .resume-item-header {
      .candidate-info {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        
        .candidate-name {
          font-size: 16px;
          font-weight: 600;
          color: #303133;
          margin: 0;
        }
        
        .score-badge {
          flex-shrink: 0;
        }
      }
    }
    
    .resume-item-content {
      .position-info {
        margin-bottom: 12px;
        
        .position-text {
          color: #606266;
          font-size: 14px;
        }
      }
      
      .resume-actions {
        display: flex;
        gap: 8px;
        
        .el-button {
          flex: 1;
        }
      }
    }
  }
  
  .pagination-container {
    padding: 16px;
    border-top: 1px solid #ebeef5;
    display: flex;
    justify-content: center;
  }
}

.resume-detail-panel {
  flex: 1;
  min-width: 0;
  
  .welcome-container {
    height: 100%;
    
    .welcome-card {
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255, 255, 255, 0.95);
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      
      .welcome-content {
        text-align: center;
        
        .welcome-icon {
          margin-bottom: 20px;
          color: #c0c4cc;
        }
        
        h2 {
          color: #303133;
          margin-bottom: 12px;
        }
        
        p {
          color: #606266;
          margin-bottom: 24px;
        }
      }
    }
  }
  
  .resume-detail-content {
    height: 100%;
    display: flex;
    flex-direction: column;
    
    .detail-header {
      background: rgba(255, 255, 255, 0.95);
      padding: 24px;
      border-radius: 16px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      
      .candidate-profile {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .profile-info {
          h3 {
            margin: 0 0 4px 0;
            color: #303133;
            font-size: 20px;
          }
          
          .current-position {
            color: #606266;
            margin: 0 0 8px 0;
            font-size: 14px;
          }
          
          .profile-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            color: #909399;
            margin-bottom: 16px;
            
            .meta-divider {
              color: #dcdfe6;
            }
          }
          
          .action-buttons {
            display: flex;
            gap: 12px;
            
            .el-button {
              border-radius: 8px;
              font-weight: 500;
              transition: all 0.3s ease;
              
              &.el-button--danger {
                background: linear-gradient(135deg, #ff6b6b, #ee5a52);
                border: none;
                
                &:hover {
                  background: linear-gradient(135deg, #ff5252, #e53935);
                  transform: translateY(-1px);
                  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
                }
              }
              
              &.el-button--primary {
                background: linear-gradient(135deg, #667eea, #764ba2);
                border: none;
                
                &:hover {
                  background: linear-gradient(135deg, #5a6fd8, #6a4190);
                  transform: translateY(-1px);
                  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                }
              }
            }
          }
        }
      }
      
      .score-section {
        text-align: center;
        
        .score-display {
          margin-bottom: 8px;
          
          .score-text {
            font-size: 14px;
            font-weight: 600;
          }
        }
        
        .score-label {
          margin: 0;
          font-size: 12px;
          color: #909399;
        }
      }
    }
    
    .detail-main {
      flex: 1;
      background: rgba(255, 255, 255, 0.95);
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      min-height: 0;
      padding: 20px;
      
      .two-column-layout {
        display: flex;
        gap: 20px;
        height: 100%;
        
        .left-column,
        .right-column {
          flex: 1;
          display: flex;
          flex-direction: column;
          background: rgba(255, 255, 255, 0.8);
          border-radius: 12px;
          border: 1px solid rgba(255, 255, 255, 0.3);
          overflow: hidden;
        }
        
        .column-header {
          background: rgba(102, 126, 234, 0.1);
          padding: 16px 20px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.2);
          
          .column-title {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            color: #667eea;
            display: flex;
            align-items: center;
            gap: 8px;
            
            .el-icon {
              font-size: 18px;
            }
          }
        }
        
        .column-content {
          flex: 1;
          padding: 20px;
          overflow-y: auto;
          
          &::-webkit-scrollbar {
            width: 6px;
          }
          
          &::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
          }
          
          &::-webkit-scrollbar-thumb {
            background: rgba(102, 126, 234, 0.3);
            border-radius: 3px;
            
            &:hover {
              background: rgba(102, 126, 234, 0.5);
            }
          }
        }
      }
    }
  }
}

.basic-info-section {
  .info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
    
    .info-item {
      display: flex;
      
      label {
        font-weight: 600;
        color: #606266;
        width: 80px;
        flex-shrink: 0;
      }
      
      span {
        color: #303133;
      }
    }
  }
  
  .skills-section,
  .highlights-section {
    margin-bottom: 24px;
    
    h4 {
      margin: 0 0 12px 0;
      color: #303133;
      font-size: 16px;
    }
    
    .skills-tags,
    .highlights-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    
    .skill-tag,
    .highlight-tag {
      margin: 0;
    }
  }
}

.resume-content-section {
  .content-display {
    line-height: 1.6;
    color: #303133;
    
    :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
      color: #303133;
      margin-top: 24px;
      margin-bottom: 12px;
    }
    
    :deep(p) {
      margin-bottom: 12px;
    }
    
    :deep(ul), :deep(ol) {
      padding-left: 20px;
      margin-bottom: 12px;
    }
  }
}

.evaluation-section {
  .evaluation-content {
    .evaluation-item {
      background: #f8f9fa;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;
      
      .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        
        .metric-name {
          margin: 0;
          color: #303133;
          font-size: 16px;
        }
      }
      
      .metric-reason {
        p {
          margin: 0;
          color: #606266;
          line-height: 1.6;
        }
      }
    }
  }
}

.loading-container,
.empty-container {
  padding: 40px 20px;
  text-align: center;
}

.upload-section {
  .jd-selector-section {
    margin-bottom: 20px;
    padding: 16px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    
    :deep(.el-form-item__label) {
      color: #333;
      font-weight: 500;
    }
    
    :deep(.el-select) {
      .el-input__wrapper {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid #dcdfe6;
        border-radius: 6px;
        
        &:hover {
          border-color: #c0c4cc;
        }
        
        &.is-focus {
          border-color: #409eff;
          box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
        }
      }
    }
  }
  
  .upload-dragger {
    width: 100%;
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .main-content {
    flex-direction: column;
  }
  
  .resume-list-panel {
    width: 100%;
    height: 400px;
  }
  
  .resume-detail-panel {
    height: 600px;
  }
}

@media (max-width: 768px) {
  .page-container {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .filters-section {
    flex-direction: column;
    gap: 8px;
  }
  
  .detail-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .info-grid {
    grid-template-columns: 1fr !important;
  }
}
</style>