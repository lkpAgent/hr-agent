<template>
  <div class="jd-generator">
    <div class="page-container">
      <!-- 简化的页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Document /></el-icon>
            智能JD生成
          </h1>
        </div>
        <div class="header-actions">
          <el-button @click="resetForm">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          <el-button type="primary" @click="generateJD" :loading="generating">
            <el-icon><Magic /></el-icon>
            {{ generating ? '生成中...' : '生成JD' }}
          </el-button>
        </div>
      </div>

      <!-- 左右布局的主要内容 -->
      <div class="main-content">
        <!-- 左侧配置面板 -->
        <div class="config-panel">
          <el-card class="config-card">
            <template #header>
              <div class="card-header">
                <el-icon><Setting /></el-icon>
                <span>职位配置</span>
              </div>
            </template>

            <el-form 
              ref="formRef" 
              :model="form" 
              :rules="rules" 
              label-width="100px"
              label-position="top"
            >
              <!-- 第一行：职位名称和工作地点 -->
              <div class="form-row">
                <el-form-item label="职位名称" prop="jobTitle">
                  <el-input 
                    v-model="form.jobTitle" 
                    placeholder="请输入职位名称，如：前端开发工程师"
                    clearable
                  />
                </el-form-item>

                <el-form-item label="工作地点" prop="location">
                  <el-select 
                    v-model="form.location" 
                    placeholder="请选择工作地点"
                    filterable
                    clearable
                    style="width: 100%"
                  >
                    <el-option 
                      v-for="city in cities" 
                      :key="city" 
                      :label="city" 
                      :value="city" 
                    />
                  </el-select>
                </el-form-item>
              </div>

              <!-- 第二行：工作经验和学历要求 -->
              <div class="form-row">
                <el-form-item label="工作经验" prop="experience">
                  <el-select 
                    v-model="form.experience" 
                    placeholder="请选择工作经验要求"
                    style="width: 100%"
                  >
                    <el-option label="不限" value="不限" />
                    <el-option label="1年以下" value="1年以下" />
                    <el-option label="1-3年" value="1-3年" />
                    <el-option label="3-5年" value="3-5年" />
                    <el-option label="5-10年" value="5-10年" />
                    <el-option label="10年以上" value="10年以上" />
                  </el-select>
                </el-form-item>

                <el-form-item label="学历要求" prop="education">
                  <el-select 
                    v-model="form.education" 
                    placeholder="请选择学历要求"
                    style="width: 100%"
                  >
                    <el-option label="不限" value="不限" />
                    <el-option label="大专" value="大专" />
                    <el-option label="本科" value="本科" />
                    <el-option label="硕士" value="硕士" />
                    <el-option label="博士" value="博士" />
                  </el-select>
                </el-form-item>
              </div>

              <!-- 第三行：薪资范围和工作类型 -->
              <div class="form-row">
                <el-form-item label="薪资范围" prop="salary">
                  <el-input 
                    v-model="form.salary" 
                    placeholder="如：10K-20K"
                    clearable
                  />
                </el-form-item>

                <el-form-item label="工作类型" prop="jobType">
                  <el-radio-group v-model="form.jobType">
                    <el-radio label="全职">全职</el-radio>
                    <el-radio label="兼职">兼职</el-radio>
                    <el-radio label="实习">实习</el-radio>
                    <el-radio label="外包">外包</el-radio>
                  </el-radio-group>
                </el-form-item>
              </div>

              <!-- 技能要求 -->
              <el-form-item label="技能要求" prop="skills">
                <el-select
                  v-model="form.skills"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  placeholder="请选择或输入技能要求"
                  style="width: 100%"
                >
                  <el-option
                    v-for="skill in commonSkills"
                    :key="skill"
                    :label="skill"
                    :value="skill"
                  />
                </el-select>
              </el-form-item>

              <!-- 公司福利 -->
              <el-form-item label="公司福利">
                <el-checkbox-group v-model="form.benefits">
                  <el-checkbox label="五险一金">五险一金</el-checkbox>
                  <el-checkbox label="年终奖">年终奖</el-checkbox>
                  <el-checkbox label="带薪年假">带薪年假</el-checkbox>
                  <el-checkbox label="弹性工作">弹性工作</el-checkbox>
                  <el-checkbox label="远程办公">远程办公</el-checkbox>
                  <el-checkbox label="股票期权">股票期权</el-checkbox>
                  <el-checkbox label="培训机会">培训机会</el-checkbox>
                  <el-checkbox label="健身房">健身房</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <!-- 其他要求 -->
              <el-form-item label="其他要求">
                <el-input
                  v-model="form.additionalRequirements"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入其他特殊要求或补充说明"
                />
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
                <span>JD预览</span>
                <div class="header-actions" v-if="generatedJD">
                  <el-button size="small" @click="copyJD">
                    <el-icon><CopyDocument /></el-icon>
                    复制
                  </el-button>
                  <el-button size="small" type="primary" @click="saveJD">
                    <el-icon><Download /></el-icon>
                    保存
                  </el-button>
                </div>
              </div>
            </template>

            <div class="preview-content">
              <div v-if="!generatedJD && !generating" class="empty-state">
                <el-icon class="empty-icon"><Document /></el-icon>
                <p>请填写左侧职位信息，然后点击"生成JD"按钮</p>
              </div>

              <div v-if="generating" class="loading-state">
                <el-icon class="loading-icon"><Loading /></el-icon>
                <p>AI正在为您生成专业的职位描述...</p>
                <div class="loading-tips">
                  <p>💡 正在分析职位要求</p>
                  <p>🎯 匹配行业标准</p>
                  <p>✨ 优化语言表达</p>
                </div>
              </div>

              <div v-if="generatedJD" class="jd-content">
                <div class="jd-section">
                  <h3>职位信息</h3>
                  <div class="job-info-grid">
                    <div class="info-item">
                      <span class="label">职位名称：</span>
                      <span class="value">{{ form.jobTitle }}</span>
                    </div>
                    <div class="info-item">
                      <span class="label">工作地点：</span>
                      <span class="value">{{ form.location }}</span>
                    </div>
                    <div class="info-item">
                      <span class="label">工作经验：</span>
                      <span class="value">{{ form.experience }}</span>
                    </div>
                    <div class="info-item">
                      <span class="label">学历要求：</span>
                      <span class="value">{{ form.education }}</span>
                    </div>
                    <div class="info-item">
                      <span class="label">薪资范围：</span>
                      <span class="value">{{ form.salary }}</span>
                    </div>
                    <div class="info-item">
                      <span class="label">工作类型：</span>
                      <span class="value">{{ form.jobType }}</span>
                    </div>
                  </div>
                </div>

                <div class="jd-section">
                  <h3>职位描述</h3>
                  <div class="jd-text" v-html="generatedJD.description"></div>
                </div>

                <div class="jd-section">
                  <h3>任职要求</h3>
                  <div class="jd-text" v-html="generatedJD.requirements"></div>
                </div>

                <div class="jd-section" v-if="form.benefits.length > 0">
                  <h3>福利待遇</h3>
                  <div class="benefits-list">
                    <el-tag 
                      v-for="benefit in form.benefits" 
                      :key="benefit" 
                      class="benefit-tag"
                      type="success"
                    >
                      {{ benefit }}
                    </el-tag>
                  </div>
                </div>

                <div class="jd-section" v-if="form.skills.length > 0">
                  <h3>技能要求</h3>
                  <div class="skills-list">
                    <el-tag 
                      v-for="skill in form.skills" 
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
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 响应式数据
const formRef = ref()
const generating = ref(false)
const generatedJD = ref(null)

// 表单数据
const form = reactive({
  jobTitle: '',
  location: '',
  experience: '',
  education: '',
  salary: '',
  jobType: '全职',
  skills: [],
  benefits: [],
  additionalRequirements: ''
})

// 表单验证规则
const rules = {
  jobTitle: [
    { required: true, message: '请输入职位名称', trigger: 'blur' }
  ],
  location: [
    { required: true, message: '请选择工作地点', trigger: 'change' }
  ],
  experience: [
    { required: true, message: '请选择工作经验要求', trigger: 'change' }
  ],
  education: [
    { required: true, message: '请选择学历要求', trigger: 'change' }
  ]
}

// 城市列表
const cities = [
  '北京', '上海', '广州', '深圳', '杭州', '南京', '苏州', '成都', 
  '武汉', '西安', '重庆', '天津', '青岛', '大连', '厦门', '宁波'
]

// 常用技能
const commonSkills = [
  'JavaScript', 'TypeScript', 'Vue.js', 'React', 'Angular', 'Node.js',
  'Python', 'Java', 'Go', 'PHP', 'C++', 'C#', 'Swift', 'Kotlin',
  'HTML', 'CSS', 'SCSS', 'Less', 'Webpack', 'Vite', 'Docker', 'Kubernetes',
  'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Git', 'Linux', 'AWS', 'Azure'
]

// 生成JD
const generateJD = async () => {
  try {
    await formRef.value.validate()
    
    generating.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 3000))
    
    // 模拟生成的JD内容
    generatedJD.value = {
      description: `
        <p>我们正在寻找一位优秀的${form.jobTitle}加入我们的团队。您将负责参与产品的设计、开发和维护工作，与团队成员协作完成高质量的项目交付。</p>
        <p>这是一个充满挑战和成长机会的职位，您将有机会接触到最新的技术栈，参与创新项目的开发，并在一个开放、包容的工作环境中发挥您的专业技能。</p>
      `,
      responsibilities: [
        '负责前端页面的设计与开发，确保用户体验的优质性',
        '与产品经理、设计师密切合作，将设计稿转化为高质量的前端代码',
        '优化前端性能，提升页面加载速度和用户交互体验',
        '参与技术方案的讨论和制定，推动创新的技术',
        '维护和改进现有代码，确保代码质量和可维护性',
        '跟进前端技术发展趋势，持续学习和应用新技术'
      ],
      requirements: [
        `${form.education}及以上学历，计算机相关专业优先`,
        `${form.experience}相关工作经验`,
        '熟练掌握HTML、CSS、JavaScript等前端基础技术',
        '熟悉Vue.js、React等主流前端框架',
        '了解前端工程化工具，如Webpack、Vite等',
        '具备良好的代码规范意识，团队协作能力',
        '有responsibility，能够承受一定的工作压力',
        '具备良好的学习能力和问题解决能力'
      ]
    }
    
    ElMessage.success('JD生成成功！')
  } catch (error) {
    console.error('生成JD失败:', error)
    ElMessage.error('生成JD失败，请重试')
  } finally {
    generating.value = false
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  generatedJD.value = null
  Object.assign(form, {
    jobTitle: '',
    location: '',
    experience: '',
    education: '',
    salary: '',
    jobType: '全职',
    skills: [],
    benefits: [],
    additionalRequirements: ''
  })
}

// 复制JD
const copyJD = async () => {
  try {
    const jdText = generateJDText()
    await navigator.clipboard.writeText(jdText)
    ElMessage.success('JD内容已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

// 保存JD
const saveJD = () => {
  const jdText = generateJDText()
  const blob = new Blob([jdText], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${form.jobTitle}_JD.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  ElMessage.success('JD已保存到本地')
}

// 生成JD文本
const generateJDText = () => {
  if (!generatedJD.value) return ''
  
  let text = `${form.jobTitle}\n\n`
  text += `工作地点：${form.location}\n`
  text += `工作经验：${form.experience}\n`
  text += `学历要求：${form.education}\n`
  text += `薪资范围：${form.salary}\n`
  text += `工作类型：${form.jobType}\n\n`
  
  text += `职位描述：\n${generatedJD.value.description.replace(/<[^>]*>/g, '')}\n\n`
  
  text += `岗位职责：\n`
  generatedJD.value.responsibilities.forEach((item, index) => {
    text += `${index + 1}. ${item}\n`
  })
  text += '\n'
  
  text += `任职要求：\n`
  generatedJD.value.requirements.forEach((item, index) => {
    text += `${index + 1}. ${item}\n`
  })
  
  if (form.benefits.length > 0) {
    text += `\n福利待遇：\n${form.benefits.join('、')}\n`
  }
  
  return text
}
</script>

<style lang="scss" scoped>
.jd-generator {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 24px;
  
  .page-container {
    max-width: 1400px;
    margin: 0 auto;
  }
  
  // 简化的页面头部
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding: 16px 24px;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    
    .header-left {
      .page-title {
        font-size: 24px;
        font-weight: 600;
        color: #ffffff;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        
        .el-icon {
          font-size: 20px;
        }
      }
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
      
      .el-button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
        
        &:not(.el-button--primary) {
          background: rgba(255, 255, 255, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.3);
          color: #ffffff;
          
          &:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
          }
        }
        
        &.el-button--primary {
          background: linear-gradient(45deg, #56ab2f, #a8e6cf);
          border: none;
          
          &:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(86, 171, 47, 0.4);
          }
        }
      }
    }
  }
  
  // 左右布局的主要内容
  .main-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    align-items: start;
    
    @media (max-width: 1200px) {
      grid-template-columns: 1fr;
      gap: 16px;
    }
  }
  
  .config-panel, .preview-panel {
    .config-card, .preview-card {
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      transition: all 0.3s ease;
      height: 100%;
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
      }
      
      :deep(.el-card__header) {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border-radius: 16px 16px 0 0;
        
        .card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-weight: 600;
          
          > span {
            display: flex;
            align-items: center;
            gap: 8px;
          }
          
          .header-actions {
            display: flex;
            gap: 8px;
            
            .el-button {
              background: rgba(255, 255, 255, 0.2);
              border: 1px solid rgba(255, 255, 255, 0.3);
              color: white;
              
              &:hover {
                background: rgba(255, 255, 255, 0.3);
              }
              
              &.el-button--primary {
                background: rgba(255, 255, 255, 0.9);
                color: #667eea;
                
                &:hover {
                  background: white;
                }
              }
            }
          }
        }
      }
      
      :deep(.el-card__body) {
        padding: 24px;
        height: calc(100% - 60px);
        overflow-y: auto;
      }
    }
  }
  
  // 预览面板特殊样式
  .preview-panel {
    .preview-card {
      min-height: 600px;
      
      :deep(.el-card__body) {
        display: flex;
        flex-direction: column;
      }
    }
    
    .preview-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      
      .empty-state, .loading-state {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
      }
      
      .jd-content {
        flex: 1;
      }
    }
  }
  
  // 表单样式
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 16px;
    
    @media (max-width: 768px) {
      grid-template-columns: 1fr;
      gap: 12px;
    }
  }
  
  :deep(.el-form-item__label) {
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 8px;
  }
  
  :deep(.el-input__wrapper) {
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    
    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    &.is-focus {
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
  }
  
  :deep(.el-select) {
    .el-input__wrapper {
      border-radius: 8px;
    }
  }
  
  :deep(.el-textarea__inner) {
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    
    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    &:focus {
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
  }
  
  :deep(.el-radio-group) {
    .el-radio {
      margin-right: 16px;
      
      .el-radio__label {
        color: #2c3e50;
        font-weight: 500;
      }
    }
  }
  
  :deep(.el-checkbox-group) {
    .el-checkbox {
      margin-right: 16px;
      margin-bottom: 8px;
      
      .el-checkbox__label {
        color: #2c3e50;
        font-weight: 500;
      }
    }
  }
  
  // 预览内容样式
  .preview-content {
    .empty-state {
      text-align: center;
      padding: 60px 20px;
      color: #95a5a6;
      
      .empty-icon {
        font-size: 64px;
        margin-bottom: 16px;
        opacity: 0.5;
      }
      
      p {
        font-size: 16px;
        margin: 0;
      }
    }
    
    .loading-state {
      text-align: center;
      padding: 60px 20px;
      color: #667eea;
      
      .loading-icon {
        font-size: 48px;
        margin-bottom: 16px;
        animation: spin 2s linear infinite;
      }
      
      p {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 20px;
      }
      
      .loading-tips {
        p {
          font-size: 14px;
          margin: 8px 0;
          opacity: 0.8;
        }
      }
    }
    
    .jd-content {
      .jd-section {
        margin-bottom: 24px;
        
        h3 {
          font-size: 18px;
          font-weight: 600;
          color: #2c3e50;
          margin-bottom: 12px;
          padding-bottom: 8px;
          border-bottom: 2px solid #ecf0f1;
          position: relative;
          
          &::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 40px;
            height: 2px;
            background: linear-gradient(45deg, #667eea, #764ba2);
          }
        }
        
        .job-info-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 12px;
          
          .info-item {
            display: flex;
            align-items: center;
            padding: 8px 12px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            
            .label {
              font-weight: 600;
              color: #34495e;
              margin-right: 8px;
            }
            
            .value {
              color: #2c3e50;
              font-weight: 500;
            }
          }
        }
        
        .jd-text {
          color: #5a6c7d;
          line-height: 1.6;
          
          p {
            margin-bottom: 12px;
          }
        }
        
        .benefits-list, .skills-list {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          
          .benefit-tag, .skill-tag {
            border-radius: 6px;
            font-weight: 500;
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .jd-generator {
    padding: 16px;
    
    .page-header {
      flex-direction: column;
      gap: 16px;
      text-align: center;
      
      .header-actions {
        justify-content: center;
      }
    }
    
    .main-content {
      grid-template-columns: 1fr;
    }
    
    .config-panel, .preview-panel {
      .config-card, .preview-card {
        :deep(.el-card__body) {
          padding: 16px;
        }
      }
    }
  }
}

// 动画效果
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
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

.config-panel, .preview-panel {
  animation: fadeInUp 0.6s ease-out;
}

.config-panel {
  animation-delay: 0.1s;
}

.preview-panel {
  animation-delay: 0.2s;
}
</style>