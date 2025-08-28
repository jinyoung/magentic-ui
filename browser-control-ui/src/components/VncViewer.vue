<template>
  <div class="vnc-viewer-container">
    <!-- VNC 상태 표시 -->
    <div class="mb-4 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="flex items-center space-x-2">
          <div :class="[
            'status-dot',
            vncStatus === 'connected' ? 'status-success' :
            vncStatus === 'connecting' ? 'status-warning' :
            vncStatus === 'error' ? 'status-error' : 'status-idle'
          ]"></div>
          <span class="text-sm font-medium text-gray-700">
            VNC: {{ vncStatusText }}
          </span>
        </div>
      </div>
      
      <div class="flex items-center space-x-2">
        <button
          @click="refreshVnc"
          :disabled="vncStatus === 'connecting'"
          class="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          새로고침
        </button>
        <button
          @click="toggleFullscreen"
          class="px-3 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          {{ isFullscreen ? '창모드' : '전체화면' }}
        </button>
      </div>
    </div>

    <!-- VNC 뷰어 -->
    <div 
      ref="vncContainer"
      :class="[
        'vnc-container relative',
        isFullscreen ? 'fixed inset-0 z-50 bg-black' : 'w-full h-96'
      ]"
    >
      <!-- 로딩 상태 -->
      <div 
        v-if="vncStatus === 'connecting'" 
        class="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg"
      >
        <div class="text-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
          <p class="text-sm text-gray-600">VNC 연결 중...</p>
        </div>
      </div>

      <!-- 오류 상태 -->
      <div 
        v-else-if="vncStatus === 'error'" 
        class="absolute inset-0 flex items-center justify-center bg-red-50 rounded-lg border-2 border-red-200"
      >
        <div class="text-center">
          <div class="text-red-500 mb-2">
            <svg class="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          <p class="text-sm text-red-700 mb-2">VNC 연결 실패</p>
          <button 
            @click="connectVnc"
            class="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
          >
            다시 연결
          </button>
        </div>
      </div>

      <!-- VNC iframe -->
      <iframe
        v-show="vncStatus === 'connected'"
        ref="vncIframe"
        :src="vncUrl"
        :class="[
          'w-full h-full border-0 rounded-lg',
          isFullscreen ? 'rounded-none' : ''
        ]"
        @load="onVncLoad"
        @error="onVncError"
      ></iframe>

      <!-- 전체화면 종료 버튼 -->
      <button
        v-if="isFullscreen"
        @click="toggleFullscreen"
        class="absolute top-4 right-4 z-10 px-4 py-2 bg-black bg-opacity-50 text-white rounded hover:bg-opacity-75"
      >
        전체화면 종료 (ESC)
      </button>
    </div>

    <!-- VNC 연결 정보 -->
    <div class="mt-2 text-xs text-gray-500">
      <p>VNC URL: {{ vncUrl }}</p>
      <p v-if="vncStatus === 'connected'">브라우저 화면을 실시간으로 볼 수 있습니다. 클릭과 키보드 입력이 가능합니다.</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VncViewer',
  props: {
    vncPort: {
      type: Number,
      default: 6080
    },
    autoConnect: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      vncStatus: 'idle', // idle, connecting, connected, error
      isFullscreen: false,
      retryCount: 0,
      maxRetries: 3
    }
  },
  computed: {
    vncUrl() {
      return `http://localhost:${this.vncPort}/vnc.html?autoconnect=true&resize=scale`
    },
    vncStatusText() {
      switch (this.vncStatus) {
        case 'idle': return '대기 중'
        case 'connecting': return '연결 중'
        case 'connected': return '연결됨'
        case 'error': return '연결 실패'
        default: return '알 수 없음'
      }
    }
  },
  mounted() {
    if (this.autoConnect) {
      this.connectVnc()
    }
    
    // ESC 키로 전체화면 종료
    document.addEventListener('keydown', this.handleKeydown)
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleKeydown)
  },
  methods: {
    connectVnc() {
      this.vncStatus = 'connecting'
      this.retryCount++
      
      // iframe 새로고침으로 연결 시도
      if (this.$refs.vncIframe) {
        this.$refs.vncIframe.src = this.vncUrl
      }
      
      // 타임아웃 설정
      setTimeout(() => {
        if (this.vncStatus === 'connecting') {
          this.vncStatus = 'error'
          
          // 자동 재시도
          if (this.retryCount < this.maxRetries) {
            setTimeout(() => {
              this.connectVnc()
            }, 2000)
          }
        }
      }, 10000) // 10초 타임아웃
    },
    
    onVncLoad() {
      // iframe이 로드되면 잠시 후 연결 상태로 변경
      setTimeout(() => {
        this.vncStatus = 'connected'
        this.retryCount = 0
        this.$emit('connected')
      }, 2000)
    },
    
    onVncError() {
      this.vncStatus = 'error'
      this.$emit('error', 'VNC 로드 실패')
    },
    
    refreshVnc() {
      this.connectVnc()
    },
    
    toggleFullscreen() {
      this.isFullscreen = !this.isFullscreen
      this.$emit('fullscreen-changed', this.isFullscreen)
    },
    
    handleKeydown(event) {
      if (event.key === 'Escape' && this.isFullscreen) {
        this.toggleFullscreen()
      }
    }
  }
}
</script>

<style scoped>
/* 컴포넌트별 스타일은 이미 style.css에 정의됨 */
</style>
