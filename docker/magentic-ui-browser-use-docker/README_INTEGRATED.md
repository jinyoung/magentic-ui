# Integrated Browser-Use Server with ProcessGPT Support

통합된 브라우저-사용 서버는 ProcessGPT Agent와 호환되는 고급 웹 브라우저 자동화 시스템입니다.

## 🚀 주요 기능

- **통합된 브라우저 세션**: 동일한 브라우저 세션을 유지하면서 여러 태스크 실행
- **ProcessGPT Agent Server 호환**: ProcessGPT SDK와 완전 호환
- **자연어 태스크 실행**: 한국어/영어로 브라우저 작업 지시 가능
- **RESTful API**: 표준 HTTP API를 통한 서비스 제공
- **Docker 컨테이너**: 격리된 환경에서 안전한 실행

## 📁 파일 구조

```
docker/magentic-ui-browser-use-docker/
├── integrated_browser_server.py      # 통합된 서버 메인 파일
├── run_integrated_server.py          # 서버 실행 스크립트
├── test_integrated_server.py         # 테스트 스크립트
├── browser_use_agent.py              # 브라우저 에이전트 클래스
├── browser-use-server.py             # 기존 서버 (호환성 유지)
├── Dockerfile                        # Docker 이미지 빌드 파일
├── supervisord.conf                  # 서비스 관리 설정
└── README_INTEGRATED.md              # 이 문서
```

## 🛠️ 설치 및 실행

### 1. Docker로 실행 (권장)

```bash
# Docker 이미지 빌드
./build.sh

# 컨테이너 실행
docker run -d \
  --name magentic-browser-integrated \
  -p 6080:6080 \
  -p 5001:5001 \
  -e OPENAI_API_KEY="your-api-key-here" \
  magentic-ui-browser-use:latest

# 통합 서버 실행 (컨테이너 내부)
docker exec -it magentic-browser-integrated python3 /app/run_integrated_server.py
```

### 2. 로컬 실행

```bash
# 필요한 패키지 설치
pip install browser-use flask flask-cors pydantic playwright

# Playwright 브라우저 설치
playwright install chromium

# 환경변수 설정
export OPENAI_API_KEY="your-api-key-here"
export DISPLAY=":99"

# 서버 실행
python3 run_integrated_server.py
```

## 🌐 API 엔드포인트

### 기본 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/health` | 헬스 체크 |
| GET | `/status` | 서버 상태 조회 |
| GET | `/test` | 테스트 엔드포인트 |
| GET | `/tasks/examples` | 태스크 예시 목록 |

### 태스크 실행 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/execute` | 일반 태스크 실행 |
| POST | `/processgpt/execute` | ProcessGPT 호환 실행 |

## 📝 사용 예시

### 1. 헬스 체크

```bash
curl http://localhost:5001/health
```

### 2. 상태 조회

```bash
curl http://localhost:5001/status
```

### 3. Google에서 Playwright 검색

```bash
curl -X POST http://localhost:5001/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "Google에서 \"playwright\" 검색하기"}'
```

### 4. ProcessGPT 호환 실행

```bash
curl -X POST http://localhost:5001/processgpt/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "GitHub 홈페이지로 이동하기",
    "parameters": {
      "timeout": 60
    }
  }'
```

## 🧪 테스트 실행

### 자동 테스트 스위트

```bash
# 서버가 실행 중인 상태에서
python3 test_integrated_server.py
```

### 개별 테스트

```python
import requests

# 헬스 체크
response = requests.get("http://localhost:5001/health")
print(response.json())

# 태스크 실행
response = requests.post("http://localhost:5001/execute", 
                        json={"task": "Google 홈페이지 방문하기"})
print(response.json())
```

## 🔧 설정

### BrowserUseAgentConfig

```python
config = BrowserUseAgentConfig(
    llm_model="gpt-4o-mini",           # 사용할 LLM 모델
    headless=False,                    # 헤드리스 모드 여부
    save_recording_path="./recordings", # 녹화 저장 경로
    max_actions=100,                   # 최대 액션 수
    display=":99"                      # X11 디스플레이
)
```

### 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 키 (필수) | - |
| `DISPLAY` | X11 디스플레이 | `:99` |
| `BROWSER_HEADLESS` | 헤드리스 모드 | `false` |

## 🚨 문제 해결

### 1. browser-use 임포트 오류

```bash
pip install browser-use
playwright install chromium
```

### 2. DISPLAY 환경변수 오류

```bash
export DISPLAY=:99
# 또는 X11 서버 시작
Xvfb :99 -screen 0 1920x1080x24 &
```

### 3. OpenAI API 키 오류

```bash
export OPENAI_API_KEY="your-actual-api-key"
```

### 4. 포트 충돌

서버가 포트 5001을 사용합니다. 다른 포트를 사용하려면:

```python
app.run(host='0.0.0.0', port=5002, debug=False)
```

## 🔄 ProcessGPT Agent Simulator 사용

```python
from processgpt_agent_sdk.simulator import ProcessGPTAgentSimulator
from integrated_browser_server import IntegratedBrowserController

# 컨트롤러 생성
controller = IntegratedBrowserController()

# 시뮬레이터 설정
simulator = ProcessGPTAgentSimulator()
simulator.register_agent('browser_agent', controller)

# 테스트 실행
result = simulator.run_agent(
    'browser_agent',
    command='execute',
    task="Google에서 'playwright' 검색하기"
)

print(result)
```

## 📊 모니터링

### 서버 로그 확인

```bash
# Docker 컨테이너 로그
docker logs magentic-browser-integrated

# 실시간 로그 모니터링
docker logs -f magentic-browser-integrated
```

### 브라우저 화면 확인

noVNC를 통해 브라우저 화면을 확인할 수 있습니다:
- URL: `http://localhost:6080`
- 비밀번호: 없음 (기본 설정)

## 🎯 예시 태스크

### 검색 작업
- "Google에서 'machine learning' 검색하기"
- "네이버에서 '날씨' 검색하고 결과 확인하기"

### 웹사이트 탐색
- "GitHub 홈페이지로 이동하기"
- "Stack Overflow에서 Python 질문 찾기"

### 데이터 수집
- "현재 페이지의 제목과 주요 링크 수집하기"
- "제품 페이지에서 가격 정보 추출하기"

### 폼 작성
- "로그인 폼에 사용자 정보 입력하기"
- "연락처 폼 작성하고 제출하기"

## 🚀 고급 사용법

### 커스텀 설정으로 서버 시작

```python
from integrated_browser_server import BrowserUseAgentConfig, IntegratedBrowserController

# 커스텀 설정
config = BrowserUseAgentConfig(
    llm_model="gpt-4",
    headless=True,
    max_actions=200,
    save_recording_path="/recordings"
)

# 컨트롤러 생성
controller = IntegratedBrowserController(config)

# 태스크 실행
result = await controller.execute_task("복잡한 웹 작업 수행하기")
```

### 배치 작업 실행

```python
tasks = [
    "Google 홈페이지 방문하기",
    "검색창에 'AI' 입력하기",
    "첫 번째 결과 클릭하기",
    "페이지 제목 확인하기"
]

for task in tasks:
    result = await controller.execute_task(task)
    print(f"태스크: {task}")
    print(f"결과: {result['success']}")
```

## 📈 성능 최적화

### 1. 브라우저 세션 재사용
- 통합된 서버는 브라우저 세션을 재사용하여 성능을 향상시킵니다.

### 2. 액션 수 제한
- `max_actions` 설정으로 무한 루프를 방지합니다.

### 3. 타임아웃 설정
- 각 요청에 적절한 타임아웃을 설정합니다.

## 🔐 보안 고려사항

1. **API 키 보호**: 환경변수로 API 키를 관리하세요.
2. **네트워크 격리**: Docker 컨테이너를 사용하여 격리된 환경에서 실행하세요.
3. **권한 제한**: 최소 권한으로 실행하세요.

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. 로그 파일 검토
2. 환경변수 설정 확인
3. 네트워크 연결 상태 확인
4. API 키 유효성 검증

---

**참고**: 이 서버는 OpenAI API를 사용하므로 API 요청 비용이 발생할 수 있습니다.
