<template>
  <div class="knowledge-management">
    <div class="header">
      <h1>知识库管理</h1>
      <p>管理和维护知识库内容</p>
    </div>

    <div class="content">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>知识库管理功能</span>
            <el-button type="primary" size="small">
              添加知识
            </el-button>
          </div>
        </template>
        
        <div class="management-content">
          <el-empty description="知识库管理功能开发中..." />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// 响应式数据
const loading = ref(false)

// 生命周期
onMounted(() => {
  console.log('知识库管理页面已加载')
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