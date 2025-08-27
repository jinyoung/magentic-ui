# Magentic UI Browser Interface

가상 브라우저 Docker 컨테이너를 관리하고 접속할 수 있는 웹 인터페이스입니다.

## 🚀 기능

- **Docker 컨테이너 관리**: 빌드, 시작, 중지, 재시작
- **실시간 상태 모니터링**: 컨테이너 상태 실시간 확인
- **noVNC 웹 접속**: 브라우저에서 직접 가상 브라우저 사용
- **Playwright 서버**: 자동화된 브라우저 제어
- **로그 관리**: 실행 로그 실시간 표시

## 📋 사전 요구사항

- Node.js 16.0.0 이상
- Docker
- Docker가 실행 중인 상태

## 🛠️ 설치 및 설정

### 1. 의존성 설치

```bash
cd browser-interface
npm install
```

### 2. Docker 이미지 빌드

```bash
npm run build-image
```

또는 직접 빌드:

```bash
cd ../docker/magentic-ui-browser-docker
docker build -t magentic-ui-browser:latest .
```

### 3. 웹 서버 시작

```bash
npm start
```

개발 모드로 실행 (자동 재시작):

```bash
npm run dev
```

## 🌐 사용법

### 웹 인터페이스 접속

1. 웹 브라우저에서 `http://localhost:3000` 접속
2. "Docker 이미지 빌드" 버튼 클릭 (최초 1회)
3. 포트 설정 확인 (기본값: noVNC 6080, Playwright 37367)
4. "컨테이너 시작" 버튼 클릭
5. 브라우저 화면에서 가상 브라우저 사용

### API 엔드포인트

#### Docker 이미지 빌드
```http
POST /api/build
```

#### 컨테이너 시작
```http
POST /api/start
Content-Type: application/json

{
  "containerName": "magentic-ui-browser",
  "vncPort": 6080,
  "playwrightPort": 37367
}
```

#### 컨테이너 중지
```http
POST /api/stop
Content-Type: application/json

{
  "containerName": "magentic-ui-browser"
}
```

#### 컨테이너 재시작
```http
POST /api/restart
Content-Type: application/json

{
  "containerName": "magentic-ui-browser",
  "vncPort": 6080,
  "playwrightPort": 37367
}
```

#### 컨테이너 상태 확인
```http
GET /api/status/{containerName}
```

#### Docker 이미지 존재 확인
```http
GET /api/image/check
```

## 🐳 Docker 컨테이너 구성

컨테이너는 다음 서비스들을 실행합니다:

- **Xvfb**: X11 가상 디스플레이 서버
- **OpenBox**: 경량 윈도우 매니저
- **x11vnc**: VNC 서버
- **noVNC**: 웹 기반 VNC 클라이언트
- **Playwright**: 브라우저 자동화 서버

### 포트 매핑

- `6080`: noVNC 웹 인터페이스
- `37367`: Playwright 웹소켓 서버

## 🔧 설정 옵션

### 환경 변수

- `PORT`: 웹 서버 포트 (기본값: 3000)
- `NODE_ENV`: 실행 환경 (development/production)

### 컨테이너 환경 변수

- `NO_VNC_PORT`: noVNC 포트
- `PLAYWRIGHT_PORT`: Playwright 포트
- `PLAYWRIGHT_WS_PATH`: Playwright 웹소켓 경로
- `DISPLAY`: X11 디스플레이

## 🎯 사용 예시

### 1. 기본 사용

```bash
# 1. 서버 시작
npm start

# 2. 브라우저에서 http://localhost:3000 접속
# 3. "Docker 이미지 빌드" 클릭
# 4. "컨테이너 시작" 클릭
# 5. 가상 브라우저 사용
```

### 2. 커스텀 포트 사용

웹 인터페이스에서 포트 번호를 변경한 후 컨테이너를 시작하세요.

### 3. Playwright 연결

```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.connectOverCDT('ws://localhost:37367/default');
  const page = await browser.newPage();
  
  await page.goto('https://example.com');
  await page.screenshot({ path: 'example.png' });
  
  await browser.close();
})();
```

## 🚨 문제 해결

### 컨테이너가 시작되지 않는 경우

1. Docker가 실행 중인지 확인
2. 포트가 이미 사용 중인지 확인
3. Docker 이미지가 빌드되었는지 확인

```bash
# Docker 상태 확인
docker info

# 포트 사용 확인
lsof -i :6080
lsof -i :37367

# 이미지 확인
docker images | grep magentic-ui-browser
```

### noVNC 연결 실패

1. 컨테이너가 완전히 시작될 때까지 대기 (약 10-15초)
2. 브라우저에서 `http://localhost:6080` 직접 접속 시도
3. 방화벽 설정 확인

### 성능 최적화

- Docker Desktop 메모리 할당량 증가 (4GB 이상 권장)
- SSD 사용 권장
- 브라우저 확장 프로그램 비활성화

## 📝 로그 확인

### 웹 인터페이스 로그
웹 인터페이스 하단의 로그 패널에서 실시간 로그 확인

### Docker 컨테이너 로그
```bash
docker logs magentic-ui-browser
```

### 서버 로그
터미널에서 `npm start` 실행 시 로그 출력

## 🤝 기여

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

MIT License - 자세한 내용은 LICENSE 파일을 참조하세요.

## 🆘 지원

문제가 발생하거나 질문이 있으시면 GitHub Issues를 통해 문의해 주세요.
