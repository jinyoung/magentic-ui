# Magentic UI WebSurfer Server

magentic-ui의 WebSurfer 기능을 추출하여 독립적인 서버로 구현한 AI 기반 브라우저 자동화 시스템입니다.

## 🚀 주요 기능

### WebSurfer 핵심 기능
- **시각적 요소 인식**: 웹페이지의 인터랙티브 요소 자동 탐지
- **Set-of-Mark**: 스크린샷에 요소 ID 마커 표시
- **자연어 명령**: LLM을 통한 직관적인 브라우저 제어
- **멀티모달 AI**: 스크린샷과 텍스트를 함께 분석

### 지원 액션
- `click`: 요소 클릭
- `input_text`: 텍스트 입력
- `scroll_up/down`: 페이지 스크롤
- `visit_url`: URL 방문
- `web_search`: 웹 검색
- `history_back`: 뒤로 가기
- `refresh_page`: 페이지 새로고침
- `stop_action`: 작업 완료
- `answer_question`: 질문 답변

## 📋 사전 요구사항

- Python 3.8 이상
- Docker (브라우저 컨테이너용)
- OpenAI API 키
- Node.js (기존 browser-interface 실행용)

## 🛠️ 설치 및 설정

### 1. 자동 설정 (권장)

```bash
cd browser-interface
./setup_websurfer.sh
```

### 2. 수동 설정

```bash
# Python 가상환경 생성
python3 -m venv venv_websurfer
source venv_websurfer/bin/activate

# 의존성 설치
pip install -r requirements_websurfer.txt

# Playwright 브라우저 설치
playwright install chromium

# 환경변수 설정
export OPENAI_API_KEY="your-openai-api-key"
```

## 🌐 사용법

### 1. Docker 브라우저 컨테이너 시작

```bash
# 기존 browser-interface 서버 시작
npm start

# 웹 인터페이스에서 Docker 컨테이너 빌드 및 시작
# http://localhost:3000 접속 후 "컨테이너 시작" 클릭
```

### 2. WebSurfer 서버 시작

```bash
source venv_websurfer/bin/activate
python magentic_websurfer_server.py
```

서버가 `http://localhost:5002`에서 실행됩니다.

### 3. 테스트 페이지 사용

브라우저에서 `websurfer-test.html` 파일을 열어 GUI로 테스트할 수 있습니다.

## 📡 API 엔드포인트

### GET /health
시스템 상태 확인
```json
{
  "status": "healthy",
  "playwright_available": true,
  "openai_available": true,
  "connected": true
}
```

### POST /connect
브라우저 연결
```json
{
  "ws_url": "ws://localhost:37367/default"
}
```

### POST /execute
자연어 태스크 실행
```json
{
  "task": "Google에서 'Playwright' 검색하기"
}
```

### POST /screenshot
스크린샷 촬영 (인터랙티브 요소 마커 포함)

### GET /page_info
현재 페이지 정보 조회

### GET /tasks/examples
예시 태스크 목록

## 🎯 사용 예시

### 기본 사용법

```python
import requests

# 브라우저 연결
requests.post('http://localhost:5002/connect', 
              json={'ws_url': 'ws://localhost:37367/default'})

# 태스크 실행
response = requests.post('http://localhost:5002/execute', 
                        json={'task': 'Google에서 Playwright 검색하기'})

result = response.json()
print(f"실행 결과: {result['action_result']['message']}")
```

### 자연어 명령 예시

- "Google에서 'Playwright' 검색하기"
- "첫 번째 검색 결과 클릭하기" 
- "이메일 입력 필드에 'test@example.com' 입력하기"
- "페이지 맨 아래로 스크롤하기"
- "로그인 버튼 클릭하기"

## 🔧 설정

### 환경 변수

```bash
# 필수
export OPENAI_API_KEY="your-openai-api-key"

# 선택사항
export WEBSURFER_PORT=5002
export WEBSURFER_HOST=0.0.0.0
export PLAYWRIGHT_WS_URL=ws://localhost:37367/default
```

### .env 파일

```env
OPENAI_API_KEY=your-openai-api-key-here
WEBSURFER_PORT=5002
WEBSURFER_HOST=0.0.0.0
PLAYWRIGHT_WS_URL=ws://localhost:37367/default
```

## 🚨 문제 해결

### 브라우저 연결 실패

1. Docker 컨테이너가 실행 중인지 확인
2. Playwright 서버 포트(37367) 확인
3. WebSocket URL 확인

```bash
# 컨테이너 상태 확인
docker ps | grep magentic-ui-browser

# 포트 확인
lsof -i :37367
```

### OpenAI API 오류

1. API 키 확인
2. 계정 크레딧 확인
3. 모델 권한 확인

### 의존성 오류

```bash
# 패키지 재설치
pip install --upgrade -r requirements_websurfer.txt

# Playwright 브라우저 재설치
playwright install chromium
```

## 🔄 기존 browser_use_server.py와의 차이점

| 기능 | browser_use_server.py | magentic_websurfer_server.py |
|------|----------------------|------------------------------|
| AI 엔진 | browser-use 라이브러리 | Magentic UI WebSurfer 로직 |
| 요소 인식 | browser-use 내장 | Set-of-Mark 시각적 마커 |
| 프롬프트 | browser-use 기본 | WebSurfer 최적화 프롬프트 |
| 스크린샷 | 기본 | 인터랙티브 요소 마커 포함 |
| 의존성 | browser-use | 최소 의존성 (playwright, openai, PIL) |

## 📈 성능 최적화

- **토큰 제한**: 텍스트 컨텍스트를 2000자로 제한
- **이미지 압축**: 스크린샷 크기 최적화
- **캐싱**: 페이지 스크립트 캐싱
- **비동기**: 모든 브라우저 작업 비동기 처리

## 🤝 기여

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

MIT License

## 🆘 지원

문제가 발생하거나 질문이 있으시면 GitHub Issues를 통해 문의해 주세요.
