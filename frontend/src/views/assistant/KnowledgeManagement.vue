<template>
  <div class="knowledge-management">
    <div class="page-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-content">
          <h1 class="page-title">
            <el-icon><Collection /></el-icon>
            知识库管理
          </h1>
          <p class="page-subtitle">管理和维护知识库内容，构建智能问答系统</p>
        </div>
        <div class="header-actions">
          <el-input
            v-model="searchQuery"
            placeholder="搜索知识库..."
            clearable
            class="search-input"
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" @click="showAddKnowledgeDialog = true">
            <el-icon><Plus /></el-icon>
            添加知识库
          </el-button>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <div class="main-content">
        <!-- 知识库列表 -->
        <div class="knowledge-list">
          <el-row :gutter="20">
            <el-col 
              v-for="kb in filteredKnowledgeBases" 
              :key="kb.id" 
              :xs="24" 
              :sm="12" 
              :md="8" 
              :lg="6"
            >
              <el-card class="knowledge-card" shadow="hover">
                <div class="card-header">
                  <div class="kb-icon">
                    <el-icon><Folder /></el-icon>
                  </div>
                  <div class="kb-actions">
                    <el-dropdown @command="handleKnowledgeAction">
                      <el-button text>
                        <el-icon><MoreFilled /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item :command="{ action: 'edit', kb }">编辑</el-dropdown-item>
                          <el-dropdown-item :command="{ action: 'upload', kb }">上传文档</el-dropdown-item>
                          <el-dropdown-item :command="{ action: 'delete', kb }" divided>删除</el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </div>
                
                <div class="kb-content">
                  <h3 class="kb-name">{{ kb.name }}</h3>
                  <p class="kb-description">{{ kb.description || '暂无描述' }}</p>
                  
                  <div class="kb-stats">
                    <div class="stat-item">
                      <el-icon><Document /></el-icon>
                      <span>{{ kb.documentCount || 0 }} 个文档</span>
                    </div>
                    <div class="stat-item">
                      <el-icon><Clock /></el-icon>
                      <span>{{ formatTime(kb.updatedAt) }}</span>
                    </div>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
          
          <!-- 空状态 -->
          <el-empty v-if="filteredKnowledgeBases.length === 0" description="暂无知识库">
            <el-button type="primary" @click="showAddKnowledgeDialog = true">
              创建第一个知识库
            </el-button>
          </el-empty>
        </div>
      </div>
    </div>

    <!-- 添加/编辑知识库对话框 -->
    <el-dialog
      v-model="showAddKnowledgeDialog"
      :title="editingKnowledge ? '编辑知识库' : '添加知识库'"
      width="500px"
      @close="resetKnowledgeForm"
    >
      <el-form :model="knowledgeForm" :rules="knowledgeRules" ref="knowledgeFormRef" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="knowledgeForm.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="knowledgeForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入知识库描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddKnowledgeDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveKnowledge" :loading="saving">
          {{ editingKnowledge ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 上传文档对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传文档"
      width="600px"
      @close="resetUploadForm"
    >
      <div class="upload-section">
        <el-upload
          ref="uploadRef"
          class="upload-demo"
          drag
          :action="uploadAction"
          :headers="uploadHeaders"
          :data="uploadData"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :before-upload="beforeUpload"
          :file-list="fileList"
          multiple
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 PDF、DOC、DOCX、TXT 格式，单个文件不超过 10MB
            </div>
          </template>
        </el-upload>
      </div>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmUpload" :loading="uploading">
          确认上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Collection, 
  Search, 
  Plus, 
  Folder, 
  MoreFilled, 
  Document, 
  Clock, 
  UploadFilled 
} from '@element-plus/icons-vue'
import { 
  getKnowledgeBases, 
  createKnowledgeBase, 
  updateKnowledgeBase, 
  deleteKnowledgeBase 
} from '@/api/knowledgeBase'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const searchQuery = ref('')
const showAddKnowledgeDialog = ref(false)
const showUploadDialog = ref(false)
const editingKnowledge = ref(null)
const knowledgeBases = ref([])
const fileList = ref([])

// 表单相关
const knowledgeFormRef = ref()
const uploadRef = ref()
const knowledgeForm = ref({
  name: '',
  description: ''
})

const knowledgeRules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

// 上传相关
const uploadAction = ref(`${import.meta.env.VITE_API_BASE_URL}/knowledge-base/upload`)
const uploadHeaders = ref({
  'Authorization': `Bearer ${localStorage.getItem('token')}`
})
const uploadData = ref({})

// 计算属性
const filteredKnowledgeBases = computed(() => {
  if (!searchQuery.value) return knowledgeBases.value
  return knowledgeBases.value.filter(kb => 
    kb.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    (kb.description && kb.description.toLowerCase().includes(searchQuery.value.toLowerCase()))
  )
})

// 方法
const loadKnowledgeBases = async () => {
  try {
    loading.value = true
    const response = await getKnowledgeBases()
    knowledgeBases.value = response.data || []
  } catch (error) {
    console.error('加载知识库失败:', error)
    ElMessage.error('加载知识库失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // 搜索逻辑已在计算属性中实现
}

const handleSaveKnowledge = async () => {
  try {
    await knowledgeFormRef.value.validate()
    saving.value = true
    
    if (editingKnowledge.value) {
      await updateKnowledgeBase(editingKnowledge.value.id, knowledgeForm.value)
      ElMessage.success('知识库更新成功')
    } else {
      await createKnowledgeBase(knowledgeForm.value)
      ElMessage.success('知识库创建成功')
    }
    
    showAddKnowledgeDialog.value = false
    await loadKnowledgeBases()
  } catch (error) {
    console.error('保存知识库失败:', error)
    ElMessage.error('保存知识库失败')
  } finally {
    saving.value = false
  }
}

const handleKnowledgeAction = async ({ action, kb }) => {
  switch (action) {
    case 'edit':
      editingKnowledge.value = kb
      knowledgeForm.value = {
        name: kb.name,
        description: kb.description || ''
      }
      showAddKnowledgeDialog.value = true
      break
      
    case 'upload':
      uploadData.value = { knowledge_base_id: kb.id }
      showUploadDialog.value = true
      break
      
    case 'delete':
      try {
        await ElMessageBox.confirm(
          `确定要删除知识库"${kb.name}"吗？此操作不可恢复。`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await deleteKnowledgeBase(kb.id)
        ElMessage.success('知识库删除成功')
        await loadKnowledgeBases()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除知识库失败:', error)
          ElMessage.error('删除知识库失败')
        }
      }
      break
  }
}

const resetKnowledgeForm = () => {
  editingKnowledge.value = null
  knowledgeForm.value = {
    name: '',
    description: ''
  }
  knowledgeFormRef.value?.resetFields()
}

const resetUploadForm = () => {
  fileList.value = []
  uploadData.value = {}
}

const beforeUpload = (file) => {
  const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
  const isAllowedType = allowedTypes.includes(file.type)
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isAllowedType) {
    ElMessage.error('只能上传 PDF、DOC、DOCX、TXT 格式的文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('上传文件大小不能超过 10MB!')
    return false
  }
  return true
}

const handleUploadSuccess = (response, file) => {
  ElMessage.success(`文件 ${file.name} 上传成功`)
}

const handleUploadError = (error, file) => {
  console.error('上传失败:', error)
  ElMessage.error(`文件 ${file.name} 上传失败`)
}

const handleConfirmUpload = () => {
  showUploadDialog.value = false
  resetUploadForm()
}

const formatTime = (time) => {
  if (!time) return '未知'
  return new Date(time).toLocaleDateString()
}

// 生命周期
onMounted(() => {
  loadKnowledgeBases()
})
</script>

<style scoped>
.knowledge-management {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.header h1 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.header p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.management-content {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>