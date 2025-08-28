import axios from 'axios'

// API 기본 설정
const BROWSER_USE_API_BASE = 'http://localhost:5001'
const DOCKER_MANAGER_API_BASE = 'http://localhost:3000'

// Axios 인스턴스 생성
const browserUseApi = axios.create({
  baseURL: BROWSER_USE_API_BASE,
  timeout: 30000, // 30초 타임아웃
  headers: {
    'Content-Type': 'application/json'
  }
})

const dockerManagerApi = axios.create({
  baseURL: DOCKER_MANAGER_API_BASE,
  timeout: 60000, // 60초 타임아웃 (빌드용)
  headers: {
    'Content-Type': 'application/json'
  }
})

// Browser-Use API 서비스
export const browserUseService = {
  // 헬스 체크
  async checkHealth() {
    try {
      const response = await browserUseApi.get('/health')
      return {
        success: true,
        data: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  },

  // 상태 조회
  async getStatus() {
    try {
      const response = await browserUseApi.get('/status')
      return {
        success: true,
        data: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  },

  // 태스크 실행
  async executeTask(task) {
    try {
      const response = await browserUseApi.post('/execute', { task })
      return {
        success: true,
        data: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || error.message,
        details: error.response?.data
      }
    }
  },

  // 태스크 예시 조회
  async getTaskExamples() {
    try {
      const response = await browserUseApi.get('/tasks/examples')
      return {
        success: true,
        data: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  },

  // 테스트 엔드포인트
  async test() {
    try {
      const response = await browserUseApi.get('/test')
      return {
        success: true,
        data: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }
}

// Docker Manager API 서비스
export const dockerManagerService = {
  // Browser-Use Docker 이미지 빌드
  async buildBrowserUseImage() {
    try {
      const response = await dockerManagerApi.post('/api/browser-use-docker/build')
      return {
        success: true,
        data: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  },

  // Browser-Use Docker 컨테이너 시작
  async startBrowserUseContainer(options = {}) {
    const {
      containerName = 'magentic-ui-browser-use',
      vncPort = 6080,
      playwrightPort = 37367,
      browserUsePort = 5001
    } = options

    try {
      const response = await dockerManagerApi.post('/api/browser-use-docker/start', {
        containerName,
        vncPort,
        playwrightPort,
        browserUsePort
      })
      return {
        success: true,
        data: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  },

  // Browser-Use Docker 컨테이너 중지
  async stopBrowserUseContainer(containerName = 'magentic-ui-browser-use') {
    try {
      const response = await dockerManagerApi.post('/api/stop', { containerName })
      return {
        success: true,
        data: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  },

  // Browser-Use Docker 헬스 체크
  async checkBrowserUseDockerHealth() {
    try {
      const response = await dockerManagerApi.get('/api/browser-use-docker/health')
      return {
        success: true,
        data: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  },

  // Browser-Use Docker 태스크 실행 (프록시)
  async executeBrowserUseTask(task) {
    try {
      const response = await dockerManagerApi.post('/api/browser-use-docker/execute', { task })
      return {
        success: true,
        data: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }
}

// 통합 서비스 (Browser-Use 직접 접근과 Docker Manager 프록시 통합)
export const integratedService = {
  // 자동으로 사용 가능한 서비스 감지하여 태스크 실행
  async executeTask(task) {
    // 먼저 직접 Browser-Use API 시도
    let result = await browserUseService.executeTask(task)
    
    if (result.success) {
      return { ...result, source: 'direct' }
    }

    // 실패하면 Docker Manager를 통한 프록시 시도
    result = await dockerManagerService.executeBrowserUseTask(task)
    
    if (result.success) {
      return { ...result, source: 'docker_proxy' }
    }

    return {
      success: false,
      error: 'Both direct and proxy access failed',
      details: result
    }
  },

  // 서비스 상태 체크
  async checkAllServices() {
    const results = {}

    // Browser-Use 직접 접근 체크
    results.browserUseDirect = await browserUseService.checkHealth()
    
    // Docker Manager를 통한 접근 체크
    results.dockerManager = await dockerManagerService.checkBrowserUseDockerHealth()

    return {
      success: results.browserUseDirect.success || results.dockerManager.success,
      services: results
    }
  }
}

export default {
  browserUseService,
  dockerManagerService,
  integratedService
}
