import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 配置NProgress
NProgress.configure({ 
  showSpinner: false,
  minimum: 0.2,
  easing: 'ease',
  speed: 500
})

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { 
      title: '登录',
      requiresAuth: false,
      hideInMenu: true
    }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: { 
          title: '工作台',
          icon: 'House',
          requiresAuth: true
        }
      },
      {
        path: 'recruitment',
        name: 'Recruitment',
        meta: { 
          title: '智能招聘',
          icon: 'UserFilled',
          requiresAuth: true
        },
        children: [
          {
            path: '',
            redirect: '/recruitment/jd-generator'
          },
          {
            path: 'jd-generator',
            name: 'JDGenerator',
            component: () => import('@/views/recruitment/JDGenerator.vue'),
            meta: { 
              title: 'JD生成',
              requiresAuth: true
            }
          },
          {
            path: 'resume-screening',
            name: 'ResumeScreening',
            component: () => import('@/views/recruitment/ResumeScreening.vue'),
            meta: { 
              title: '简历筛选',
              requiresAuth: true
            }
          },
          {
            path: 'smart-interview',
            name: 'SmartInterview',
            component: () => import('@/views/recruitment/SmartInterview.vue'),
            meta: { 
              title: '智能面试',
              requiresAuth: true
            }
          }
        ]
      },
      {
        path: 'training',
        name: 'Training',
        meta: { 
          title: '智能培训',
          icon: 'Reading',
          requiresAuth: true
        },
        children: [
          {
            path: '',
            redirect: '/training/exam-generator'
          },
          {
            path: 'exam-generator',
            name: 'ExamGenerator',
            component: () => import('@/views/training/ExamGenerator.vue'),
            meta: { 
              title: '试卷生成',
              requiresAuth: true
            }
          },
          {
            path: 'exam-management',
            name: 'ExamManagement',
            component: () => import('@/views/training/ExamManagement.vue'),
            meta: { 
              title: '考试管理',
              requiresAuth: true
            }
          } 
        ]
      },
      {
        path: 'assistant',
        name: 'Assistant',
        meta: { 
          title: '知识助理',
          icon: 'ChatDotRound',
          requiresAuth: true
        },
        children: [
          {
            path: '',
            redirect: '/assistant/qa'
          },
          {
            path: 'qa',
            name: 'KnowledgeQA',
            component: () => import('@/views/assistant/KnowledgeAssistant.vue'),
            meta: { 
              title: '知识问答',
              requiresAuth: true
            }
          },
          {
            path: 'management',
            name: 'KnowledgeManagement',
            component: () => import('@/views/assistant/KnowledgeBase.vue'),
            meta: { 
              title: '知识库管理',
              requiresAuth: true
            }
          }
        ]
      },
     
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/Profile.vue'),
        meta: { 
          title: '个人中心',
          icon: 'User',
          requiresAuth: true,
          hideInMenu: true
        }
      }
    ]
  },
  {
    path: '/exam-share/:examId',
    name: 'ExamShare',
    component: () => import('@/views/exam/ExamShare.vue'),
    meta: { 
      title: '试卷分享',
      requiresAuth: false,
      hideInMenu: true
    }
  },
  {
    path: '/exam-result/:examResultId',
    name: 'ExamResult',
    component: () => import('@/views/exam/ExamResult.vue'),
    meta: { 
      title: '考试结果',
      requiresAuth: false,
      hideInMenu: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFound.vue'),
    meta: { 
      title: '页面不存在',
      hideInMenu: true
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  NProgress.start()
  
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - HR Agent`
  }
  
  // 如果需要认证，先检查认证状态
  if (requiresAuth) {
    await authStore.checkAuth()
    
    if (!authStore.isAuthenticated) {
      // 需要登录但未登录，跳转到登录页
      next('/login')
      return
    }
  }
  
  if (to.path === '/login' && authStore.isAuthenticated) {
    // 已登录用户访问登录页，跳转到首页
    next('/')
  } else {
    next()
  }
})

router.afterEach(() => {
  NProgress.done()
})

export default router