# Browser Control UI

Vue.js 기반의 AI 브라우저 자동화 제어 센터입니다. Browser-Use API와 VNC를 통해 실시간으로 가상 브라우저를 제어하고 모니터링할 수 있는 웹 인터페이스를 제공합니다.

## 🌟 주요 기능

### 🖥️ 실시간 브라우저 뷰어
- **VNC 통합**: 실시간으로 브라우저 화면을 웹에서 확인
- **전체화면 모드**: 몰입형 브라우저 조작 경험
- **상호작용**: 마우스 클릭과 키보드 입력 지원

### 🤖 AI 브라우저 자동화
- **자연어 명령**: 일반 언어로 브라우저 태스크 실행
- **예시 태스크**: 미리 정의된 다양한 자동화 시나리오
- **실시간 피드백**: 태스크 실행 결과 즉시 확인

### 📊 상태 모니터링
- **서비스 상태**: Browser-Use API, Docker Manager, VNC 연결 상태 실시간 모니터링
- **실행 히스토리**: 모든 태스크 실행 기록 보관
- **오류 처리**: 상세한 오류 메시지와 해결 방법 제시

### 🐳 Docker 통합 관리
- **원클릭 빌드**: Browser-Use Docker 이미지 자동 빌드
- **컨테이너 관리**: 시작/중지/재시작 제어
- **서비스 자동 감지**: 여러 백엔드 서비스 중 사용 가능한 것 자동 선택

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
npm install
```

### 2. 개발 서버 실행
```bash
npm run dev
```

### 3. 브라우저에서 접속
```
http://localhost:5173
```

## 🔧 설정

### 환경 요구사항
- Node.js 18.17.0+ (권장: 20.19.0+)
- 실행 중인 Browser-Use Docker 컨테이너 또는 Browser-Use API 서버
- Docker Manager 서비스 (선택사항)

### API 엔드포인트 설정

`src/services/browserUseApi.js` 파일에서 API 엔드포인트를 수정할 수 있습니다:

```javascript
const BROWSER_USE_API_BASE = 'http://localhost:5001'  // Browser-Use API
const DOCKER_MANAGER_API_BASE = 'http://localhost:3000'  // Docker Manager
```

## 📋 사용법

### 1. 서비스 시작

먼저 백엔드 서비스를 시작하세요:

```bash
# Browser-Use Docker 컨테이너 시작
cd ../docker/magentic-ui-browser-use-docker
./quick-build.sh

# 또는 Docker Manager를 통해 시작
cd ../browser-interface
node docker-manager.js
```

### 2. 웹 UI 접속

브라우저에서 `http://localhost:5173`에 접속하면 다음을 확인할 수 있습니다:

- **좌측 패널**: 태스크 입력 및 제어
- **우측 패널**: 실시간 VNC 브라우저 뷰어
- **하단 패널**: 실행 히스토리 및 로그

### 3. 태스크 실행

#### 예시 태스크 사용
미리 정의된 예시 태스크를 클릭하여 빠르게 실행할 수 있습니다:
- "Google에서 'browser automation' 검색하기"
- "GitHub 홈페이지로 이동하기"
- "현재 페이지의 제목과 주요 내용 요약하기"

#### 커스텀 태스크 입력
텍스트 영역에 자연어로 원하는 작업을 입력하세요:
- "네이버에서 '인공지능' 뉴스 검색하기"
- "Amazon에서 '맥북' 검색하고 첫 번째 상품 클릭하기"
- "현재 페이지를 아래로 스크롤하고 링크 목록 가져오기"

## 🎨 UI 컴포넌트

### VncViewer.vue
실시간 VNC 스트리밍을 위한 컴포넌트
- 자동 연결 및 재연결
- 전체화면 모드 지원
- 연결 상태 모니터링

### TaskControlPanel.vue
태스크 제어를 위한 메인 패널
- 태스크 입력 및 실행
- 서비스 상태 모니터링
- Docker 컨테이너 관리
- 예시 태스크 제공

### App.vue
메인 애플리케이션 컴포넌트
- 전체 레이아웃 관리
- 알림 시스템
- 히스토리 관리

## 🔌 API 통합

### Browser-Use API
```javascript
import { browserUseService } from './services/browserUseApi.js'

// 태스크 실행
const result = await browserUseService.executeTask("Google 검색하기")

// 상태 확인
const health = await browserUseService.checkHealth()
```

### Docker Manager API
```javascript
import { dockerManagerService } from './services/browserUseApi.js'

// 컨테이너 시작
const result = await dockerManagerService.startBrowserUseContainer()

// 이미지 빌드
const buildResult = await dockerManagerService.buildBrowserUseImage()
```

## 🛠 개발

### 프로젝트 구조
```
browser-control-ui/
├── src/
│   ├── components/          # Vue 컴포넌트
│   │   ├── VncViewer.vue   # VNC 뷰어
│   │   └── TaskControlPanel.vue  # 제어 패널
│   ├── services/           # API 서비스
│   │   └── browserUseApi.js  # API 통신 로직
│   ├── App.vue            # 메인 앱
│   ├── main.js            # 엔트리 포인트
│   └── style.css          # 글로벌 스타일
├── public/                # 정적 파일
├── package.json          # 프로젝트 설정
└── README.md            # 이 파일
```

### 빌드 및 배포
```bash
# 프로덕션 빌드
npm run build

# 빌드 결과 미리보기
npm run preview
```

## 🔧 커스터마이징

### 테마 수정
`src/style.css`에서 Tailwind CSS 클래스를 사용하여 스타일을 수정할 수 있습니다.

### 새로운 태스크 예시 추가
`TaskControlPanel.vue`의 `taskExamples` 배열에 새로운 예시를 추가하세요:

```javascript
taskExamples: [
  {
    title: '새로운 태스크',
    task: '실행할 자연어 명령',
    description: '태스크에 대한 설명'
  }
]
```

### API 엔드포인트 변경
`src/services/browserUseApi.js`에서 기본 URL을 수정하세요.

## 🐛 문제 해결

### VNC 연결 실패
1. Docker 컨테이너가 실행 중인지 확인
2. 포트 6080이 사용 가능한지 확인
3. 브라우저에서 `http://localhost:6080`에 직접 접속 테스트

### API 연결 실패
1. Browser-Use API 서비스 상태 확인: `curl http://localhost:5001/health`
2. CORS 설정 확인
3. 네트워크 방화벽 설정 확인

### 태스크 실행 실패
1. OpenAI API 키가 설정되어 있는지 확인
2. Docker 컨테이너 로그 확인: `docker logs container-name`
3. 태스크 명령이 명확하고 구체적인지 확인

## 📈 향후 계획

- [ ] 태스크 스케줄링 기능
- [ ] 다중 브라우저 세션 지원
- [ ] 태스크 템플릿 저장/로드
- [ ] 성능 모니터링 대시보드
- [ ] 협업 기능 (다중 사용자)

## 🤝 기여

이 프로젝트에 기여하고 싶으시다면:
1. Fork 하기
2. Feature 브랜치 생성
3. 변경사항 커밋
4. Pull Request 생성

## 📄 라이선스

MIT License - 자세한 내용은 LICENSE 파일을 참조하세요.