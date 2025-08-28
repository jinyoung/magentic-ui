<template>
  <div class="task-control-panel bg-white rounded-lg shadow-lg p-6">
    <!-- 헤더 -->
    <div class="mb-6">
      <h2 class="text-xl font-bold text-gray-900 mb-2">Browser Automation Control</h2>
      <p class="text-sm text-gray-600">자연어로 브라우저 자동화 태스크를 실행하세요</p>
    </div>

    <!-- 서비스 상태 -->
    <div class="mb-6">
      <h3 class="text-sm font-medium text-gray-700 mb-2">서비스 상태</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div class="flex items-center space-x-2 p-2 bg-gray-50 rounded">
          <div :class="[
            'status-dot',
            serviceStatus.browserUse ? 'status-success' : 'status-error'
          ]"></div>
          <span class="text-xs">Browser-Use API</span>
        </div>
        <div class="flex items-center space-x-2 p-2 bg-gray-50 rounded">
          <div :class="[
            'status-dot',
            serviceStatus.dockerManager ? 'status-success' : 'status-error'
          ]"></div>
          <span class="text-xs">Docker Manager</span>
        </div>
      </div>
      <button
        @click="checkServices"
        :disabled="checkingServices"
        class="mt-2 px-3 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50"
      >
        {{ checkingServices ? '확인 중...' : '상태 확인' }}
      </button>
    </div>

    <!-- 태스크 입력 -->
    <div class="mb-6">
      <label for="task-input" class="block text-sm font-medium text-gray-700 mb-2">
        실행할 태스크
      </label>
      <div class="space-y-3">
        <textarea
          id="task-input"
          v-model="taskInput"
          :disabled="isExecuting"
          placeholder="예: Google에서 'browser automation' 검색하기"
          rows="3"
          class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        ></textarea>
        
        <div class="flex space-x-2">
          <button
            @click="executeTask"
            :disabled="!taskInput.trim() || isExecuting"
            class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isExecuting" class="flex items-center justify-center">
              <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              실행 중...
            </span>
            <span v-else>태스크 실행</span>
          </button>
          
          <button
            @click="clearTask"
            :disabled="isExecuting"
            class="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            지우기
          </button>
        </div>
      </div>
    </div>

    <!-- 예시 태스크 -->
    <div class="mb-6">
      <h3 class="text-sm font-medium text-gray-700 mb-3">예시 태스크</h3>
      <div class="grid grid-cols-1 gap-2">
        <button
          v-for="example in taskExamples"
          :key="example.task"
          @click="selectExample(example.task)"
          :disabled="isExecuting"
          class="text-left p-3 border border-gray-200 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <div class="font-medium text-sm text-gray-900">{{ example.title }}</div>
          <div class="text-xs text-gray-500 mt-1">{{ example.description }}</div>
          <div class="text-xs text-blue-600 mt-1 font-mono">{{ example.task }}</div>
        </button>
      </div>
    </div>

    <!-- 실행 결과 -->
    <div v-if="lastResult" class="mb-6">
      <h3 class="text-sm font-medium text-gray-700 mb-2">실행 결과</h3>
      <div :class="[
        'p-3 rounded-md border',
        lastResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
      ]">
        <div class="flex items-start space-x-2">
          <div :class="[
            'status-dot flex-shrink-0 mt-1',
            lastResult.success ? 'status-success' : 'status-error'
          ]"></div>
          <div class="flex-1 min-w-0">
            <p :class="[
              'text-sm font-medium',
              lastResult.success ? 'text-green-800' : 'text-red-800'
            ]">
              {{ lastResult.success ? '성공' : '실패' }}
            </p>
            <p :class="[
              'text-xs mt-1',
              lastResult.success ? 'text-green-700' : 'text-red-700'
            ]">
              {{ lastResult.message || lastResult.error }}
            </p>
            <div v-if="lastResult.data && lastResult.data.result" class="mt-2">
              <p class="text-xs text-gray-600 font-medium">상세 결과:</p>
              <pre class="text-xs text-gray-700 mt-1 whitespace-pre-wrap">{{ lastResult.data.result }}</pre>
            </div>
            <div v-if="lastResult.timestamp" class="mt-2">
              <p class="text-xs text-gray-500">{{ formatTimestamp(lastResult.timestamp) }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Docker 관리 -->
    <div class="border-t pt-6">
      <h3 class="text-sm font-medium text-gray-700 mb-3">Docker 컨테이너 관리</h3>
      <div class="grid grid-cols-2 gap-2">
        <button
          @click="buildContainer"
          :disabled="isBuildingContainer"
          class="px-3 py-2 text-xs bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50"
        >
          {{ isBuildingContainer ? '빌드 중...' : '이미지 빌드' }}
        </button>
        <button
          @click="startContainer"
          :disabled="isManagingContainer"
          class="px-3 py-2 text-xs bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
        >
          {{ isManagingContainer ? '처리 중...' : '컨테이너 시작' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { browserUseService, dockerManagerService, integratedService } from '../services/browserUseApi.js'

export default {
  name: 'TaskControlPanel',
  data() {
    return {
      taskInput: '',
      isExecuting: false,
      lastResult: null,
      serviceStatus: {
        browserUse: false,
        dockerManager: false
      },
      checkingServices: false,
      taskExamples: [
        {
          title: '구글 검색',
          task: 'Google에서 "browser automation" 검색하기',
          description: '구글에서 검색어를 입력하고 검색 결과를 확인합니다'
        },
        {
          title: '웹사이트 이동',
          task: 'GitHub 홈페이지로 이동하기',
          description: 'GitHub 메인 페이지로 이동합니다'
        },
        {
          title: '네이버 검색',
          task: '네이버에서 "Vue.js" 검색하기',
          description: '네이버 검색 엔진을 사용하여 검색합니다'
        },
        {
          title: '정보 수집',
          task: '현재 페이지의 제목과 주요 내용 요약하기',
          description: '현재 페이지의 핵심 정보를 추출합니다'
        }
      ],
      isBuildingContainer: false,
      isManagingContainer: false
    }
  },
  mounted() {
    this.checkServices()
    this.loadTaskExamples()
  },
  methods: {
    async executeTask() {
      if (!this.taskInput.trim()) return
      
      this.isExecuting = true
      this.lastResult = null
      
      try {
        const result = await integratedService.executeTask(this.taskInput.trim())
        this.lastResult = {
          ...result,
          timestamp: new Date().toISOString(),
          message: result.success ? '태스크가 성공적으로 실행되었습니다' : result.error
        }
        
        this.$emit('task-executed', {
          task: this.taskInput.trim(),
          result: this.lastResult
        })
      } catch (error) {
        this.lastResult = {
          success: false,
          error: error.message,
          timestamp: new Date().toISOString(),
          message: '태스크 실행 중 오류가 발생했습니다'
        }
      } finally {
        this.isExecuting = false
      }
    },

    async checkServices() {
      this.checkingServices = true
      
      try {
        const browserUseHealth = await browserUseService.checkHealth()
        const dockerManagerHealth = await dockerManagerService.checkBrowserUseDockerHealth()
        
        this.serviceStatus = {
          browserUse: browserUseHealth.success,
          dockerManager: dockerManagerHealth.success
        }
        
        this.$emit('service-status-changed', this.serviceStatus)
      } catch (error) {
        console.error('Service check failed:', error)
      } finally {
        this.checkingServices = false
      }
    },

    async loadTaskExamples() {
      try {
        const result = await browserUseService.getTaskExamples()
        if (result.success && result.data.examples) {
          this.taskExamples = result.data.examples
        }
      } catch (error) {
        console.error('Failed to load task examples:', error)
      }
    },

    selectExample(task) {
      this.taskInput = task
    },

    clearTask() {
      this.taskInput = ''
      this.lastResult = null
    },

    async buildContainer() {
      this.isBuildingContainer = true
      
      try {
        const result = await dockerManagerService.buildBrowserUseImage()
        if (result.success) {
          this.$emit('notification', {
            type: 'success',
            message: 'Docker 이미지가 성공적으로 빌드되었습니다'
          })
        } else {
          throw new Error(result.error)
        }
      } catch (error) {
        this.$emit('notification', {
          type: 'error',
          message: `Docker 이미지 빌드 실패: ${error.message}`
        })
      } finally {
        this.isBuildingContainer = false
      }
    },

    async startContainer() {
      this.isManagingContainer = true
      
      try {
        const result = await dockerManagerService.startBrowserUseContainer()
        if (result.success) {
          this.$emit('notification', {
            type: 'success',
            message: 'Docker 컨테이너가 성공적으로 시작되었습니다'
          })
          
          // 잠시 후 서비스 상태 다시 확인
          setTimeout(() => {
            this.checkServices()
          }, 5000)
        } else {
          throw new Error(result.error)
        }
      } catch (error) {
        this.$emit('notification', {
          type: 'error',
          message: `Docker 컨테이너 시작 실패: ${error.message}`
        })
      } finally {
        this.isManagingContainer = false
      }
    },

    formatTimestamp(timestamp) {
      return new Date(timestamp).toLocaleString('ko-KR')
    }
  }
}
</script>
