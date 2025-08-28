<template>
  <div class="app min-h-screen bg-gray-50">
    <!-- 헤더 -->
    <header class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <div class="flex items-center space-x-3">
            <div class="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
              </svg>
            </div>
            <div>
              <h1 class="text-xl font-bold text-gray-900">Browser Control Center</h1>
              <p class="text-sm text-gray-500">AI-Powered Browser Automation</p>
            </div>
          </div>
          
          <div class="flex items-center space-x-4">
            <!-- 전체 상태 표시 -->
            <div class="flex items-center space-x-2">
              <div :class="[
                'status-dot',
                overallStatus === 'healthy' ? 'status-success' :
                overallStatus === 'partial' ? 'status-warning' : 'status-error'
              ]"></div>
              <span class="text-sm text-gray-700">
                {{ overallStatusText }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- 메인 컨텐츠 -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- 알림 표시 -->
      <div v-if="notification" class="mb-6">
        <div :class="[
          'p-4 rounded-md border',
          notification.type === 'success' ? 'bg-green-50 border-green-200 text-green-700' :
          notification.type === 'warning' ? 'bg-yellow-50 border-yellow-200 text-yellow-700' :
          'bg-red-50 border-red-200 text-red-700'
        ]">
          <div class="flex items-center justify-between">
            <p class="text-sm">{{ notification.message }}</p>
            <button @click="closeNotification" class="text-gray-400 hover:text-gray-600">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <!-- 컨트롤 패널 (왼쪽) -->
        <div class="space-y-6">
          <TaskControlPanel
            @task-executed="onTaskExecuted"
            @service-status-changed="onServiceStatusChanged"
            @notification="showNotification"
          />
        </div>

        <!-- VNC 뷰어 (오른쪽) -->
        <div class="space-y-6">
          <div class="bg-white rounded-lg shadow-lg p-6">
            <div class="mb-4">
              <h2 class="text-lg font-semibold text-gray-900">가상 브라우저</h2>
              <p class="text-sm text-gray-600">실시간으로 브라우저 화면을 보고 조작할 수 있습니다</p>
            </div>
            
            <VncViewer
              :vnc-port="6080"
              :auto-connect="true"
              @connected="onVncConnected"
              @error="onVncError"
              @fullscreen-changed="onVncFullscreenChanged"
            />
          </div>
        </div>
      </div>

      <!-- 로그 및 히스토리 (하단) -->
      <div class="mt-8">
        <div class="bg-white rounded-lg shadow-lg p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-gray-900">실행 히스토리</h2>
            <button
              @click="clearHistory"
              :disabled="taskHistory.length === 0"
              class="px-3 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              히스토리 지우기
            </button>
          </div>
          
          <div v-if="taskHistory.length === 0" class="text-center py-8 text-gray-500">
            <svg class="h-8 w-8 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            <p class="text-sm">아직 실행된 태스크가 없습니다</p>
          </div>
          
          <div v-else class="space-y-3 max-h-60 overflow-y-auto">
            <div
              v-for="(item, index) in taskHistory"
              :key="index"
              :class="[
                'p-3 rounded-md border',
                item.result.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
              ]"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-900 truncate">{{ item.task }}</p>
                  <p :class="[
                    'text-xs mt-1',
                    item.result.success ? 'text-green-700' : 'text-red-700'
                  ]">
                    {{ item.result.message }}
                  </p>
                </div>
                <div class="flex items-center space-x-2 ml-4">
                  <div :class="[
                    'status-dot',
                    item.result.success ? 'status-success' : 'status-error'
                  ]"></div>
                  <span class="text-xs text-gray-500">
                    {{ formatTime(item.timestamp) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 푸터 -->
    <footer class="bg-white border-t mt-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="text-center text-sm text-gray-500">
          <p>Magentic UI Browser Control Center - AI를 활용한 브라우저 자동화 플랫폼</p>
          <p class="mt-1">Vue.js + Browser-Use + Docker를 이용한 통합 솔루션</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
import TaskControlPanel from './components/TaskControlPanel.vue'
import VncViewer from './components/VncViewer.vue'

export default {
  name: 'App',
  components: {
    VncViewer,
    TaskControlPanel
  },
  data() {
    return {
      serviceStatus: {
        browserUse: false,
        dockerManager: false,
        vnc: false
      },
      taskHistory: [],
      notification: null,
      notificationTimeout: null
    }
  },
  computed: {
    overallStatus() {
      const { browserUse, dockerManager, vnc } = this.serviceStatus
      if (browserUse && vnc) return 'healthy'
      if (dockerManager && vnc) return 'healthy'
      if (vnc || browserUse || dockerManager) return 'partial'
      return 'error'
    },
    overallStatusText() {
      switch (this.overallStatus) {
        case 'healthy': return '모든 서비스 정상'
        case 'partial': return '일부 서비스 이용 가능'
        case 'error': return '서비스 연결 필요'
        default: return '상태 확인 중'
      }
    }
  },
  methods: {
    onTaskExecuted(event) {
      this.taskHistory.unshift({
        task: event.task,
        result: event.result,
        timestamp: new Date()
      })
      
      // 히스토리는 최대 50개까지만 유지
      if (this.taskHistory.length > 50) {
        this.taskHistory = this.taskHistory.slice(0, 50)
      }
    },
    
    onServiceStatusChanged(status) {
      this.serviceStatus = {
        ...this.serviceStatus,
        ...status
      }
    },
    
    onVncConnected() {
      this.serviceStatus.vnc = true
      this.showNotification({
        type: 'success',
        message: 'VNC 브라우저 뷰어가 연결되었습니다'
      })
    },
    
    onVncError(error) {
      this.serviceStatus.vnc = false
      this.showNotification({
        type: 'error',
        message: `VNC 연결 실패: ${error}`
      })
    },
    
    onVncFullscreenChanged(isFullscreen) {
      if (isFullscreen) {
        this.showNotification({
          type: 'success',
          message: '전체화면 모드로 전환되었습니다. ESC 키로 종료할 수 있습니다.'
        })
      }
    },
    
    showNotification(notification) {
      this.notification = notification
      
      // 기존 타이머 클리어
      if (this.notificationTimeout) {
        clearTimeout(this.notificationTimeout)
      }
      
      // 5초 후 자동 닫기
      this.notificationTimeout = setTimeout(() => {
        this.closeNotification()
      }, 5000)
    },
    
    closeNotification() {
      this.notification = null
      if (this.notificationTimeout) {
        clearTimeout(this.notificationTimeout)
        this.notificationTimeout = null
      }
    },
    
    clearHistory() {
      this.taskHistory = []
      this.showNotification({
        type: 'success',
        message: '실행 히스토리가 지워졌습니다'
      })
    },
    
    formatTime(date) {
      return date.toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }
  }
}
</script>

<style>
#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
</style>