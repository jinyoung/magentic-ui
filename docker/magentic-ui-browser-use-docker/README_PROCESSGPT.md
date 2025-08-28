# ProcessGPT Browser Automation Server

ProcessGPT SDK와 호환되는 브라우저 자동화 서버입니다. Google에서 'playwright' 검색 등의 웹 브라우저 자동화 작업을 자연어로 수행할 수 있습니다.

## 🚀 주요 기능

- **ProcessGPT SDK 호환**: AgentExecutor 인터페이스 구현
- **Browser-Use 통합**: 자연어로 브라우저 제어
- **Docker 컨테이너 지원**: 격리된 환경에서 안전한 실행
- **실시간 모니터링**: noVNC를 통한 브라우저 화면 확인
- **자동 폴링**: 작업 큐 모니터링 및 자동 실행

## 📁 파일 구조

```
docker/magentic-ui-browser-use-docker/
├── processgpt_browser_server.py              # ProcessGPT SDK 버전 (Supabase 필요)
├── processgpt_browser_server_standalone.py   # 독립실행형 버전 (데모용)
├── browser_use_agent_executor.py             # AgentExecutor 구현
├── test_processgpt_integration.py            # 통합 테스트
├── docker_run_processgpt.sh                  # Docker 실행 스크립트
├── .env                                       # 환경변수 설정
├── Dockerfile                                 # Docker 이미지 정의
├── supervisord.conf                           # 서비스 관리 설정
└── README_PROCESSGPT.md                       # 이 문서
```

## 🛠️ 빠른 시작

### 1. 환경변수 설정

`.env` 파일이 이미 생성되어 OpenAI API 키가 설정되어 있습니다:

```bash
# 설정 확인
cat .env
```

### 2. 로컬 실행

```bash
# 필요한 패키지 설치
pip install browser-use playwright python-dotenv

# Playwright 브라우저 설치
playwright install chromium

# 독립실행형 서버 실행
python3 processgpt_browser_server_standalone.py
```

### 3. Docker 실행

```bash
# Docker 빌드 및 실행 (자동화 스크립트)
./docker_run_processgpt.sh

# 또는 수동 실행
docker build -t magentic-ui-processgpt-browser:latest .
docker run -d \
  --name magentic-processgpt-browser \
  -p 6080:6080 -p 5001:5001 \
  -e OPENAI_API_KEY="your-api-key" \
  magentic-ui-processgpt-browser:latest
```

## 🌐 접속 정보

### 포트 매핑
- **6080**: noVNC (브라우저 화면 확인)
- **5001**: Browser-Use API 서버
- **37367**: Playwright 서버

### 접속 URL
- noVNC: http://localhost:6080
- API 헬스체크: http://localhost:5001/health
- API 상태: http://localhost:5001/status

## 📝 지원되는 작업 예시

### 검색 작업
```
Google에서 'playwright' 검색하기
네이버에서 '날씨' 검색하고 결과 확인하기
Bing에서 'browser automation' 찾기
```

### 웹사이트 탐색
```
GitHub 홈페이지로 이동하기
Stack Overflow 방문하기
현재 페이지의 제목과 주요 내용 요약하기
```

### 데이터 수집
```
현재 페이지의 모든 링크 수집하기
제품 페이지에서 가격 정보 추출하기
뉴스 사이트에서 헤드라인 가져오기
```

## 🔧 설정

### 환경변수

| 변수명 | 설명 | 기본값 | 필수 |
|--------|------|--------|------|
| `OPENAI_API_KEY` | OpenAI API 키 | - | ✅ |
| `SUPABASE_URL` | Supabase 프로젝트 URL | - | ⚠️ |
| `SUPABASE_ANON_KEY` | Supabase 익명 키 | - | ⚠️ |
| `LLM_MODEL` | 사용할 LLM 모델 | `gpt-4o-mini` | ❌ |
| `BROWSER_HEADLESS` | 헤드리스 모드 | `false` | ❌ |
| `MAX_ACTIONS` | 최대 액션 수 | `50` | ❌ |
| `TASK_TIMEOUT` | 태스크 타임아웃(초) | `120` | ❌ |
| `POLLING_INTERVAL` | 폴링 간격(초) | `5` | ❌ |

⚠️ Supabase 환경변수는 ProcessGPT SDK 사용 시에만 필요합니다.

### AgentExecutor 설정

```python
config = {
    "llm_model": "gpt-4o-mini",
    "headless": False,
    "max_actions": 50,
    "timeout": 120,
    "save_recording_path": "./recordings"
}
```

## 🧪 테스트

### 통합 테스트 실행

```bash
python3 test_processgpt_integration.py
```

### API 테스트

```bash
# 헬스 체크
curl http://localhost:5001/health

# 상태 확인
curl http://localhost:5001/status

# 작업 실행 (기존 browser-use-server API)
curl -X POST http://localhost:5001/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "Google에서 playwright 검색하기"}'
```

## 📊 모니터링

### 실시간 로그 확인

```bash
# Docker 로그
docker logs -f magentic-processgpt-browser

# 독립실행형 서버 로그
# 터미널에서 직접 출력됨
```

### 브라우저 화면 확인

noVNC를 통해 실제 브라우저 화면을 확인할 수 있습니다:
1. http://localhost:6080 접속
2. 비밀번호 없이 Connect 클릭
3. 브라우저 자동화 과정 실시간 확인

## 🔄 ProcessGPT SDK와 연동

### 완전한 ProcessGPT 환경 설정

1. **Supabase 프로젝트 생성**
   ```bash
   # https://supabase.com에서 프로젝트 생성
   # Settings > API에서 URL과 anon key 복사
   ```

2. **환경변수 업데이트**
   ```bash
   # .env 파일 편집
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   ```

3. **ProcessGPT SDK 서버 실행**
   ```bash
   python3 processgpt_browser_server.py
   ```

### Supabase 스키마 설정

```sql
-- todolist 테이블 생성
CREATE TABLE IF NOT EXISTS todolist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    activity_name TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING',
    agent_orch TEXT DEFAULT 'browser_automation_agent',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 테스트 작업 삽입
INSERT INTO todolist (user_id, activity_name, description, status, agent_orch)
VALUES ('test-user', 'playwright_search', 'Google에서 playwright 검색하기', 'PENDING', 'browser_automation_agent');
```

## 🚨 문제 해결

### 일반적인 문제

1. **API 키 오류**
   ```bash
   export OPENAI_API_KEY="your-actual-api-key"
   # 또는 .env 파일 확인
   ```

2. **브라우저 실행 오류**
   ```bash
   # Playwright 재설치
   playwright install chromium --force
   ```

3. **Docker 실행 오류**
   ```bash
   # 기존 컨테이너 정리
   docker stop magentic-processgpt-browser
   docker rm magentic-processgpt-browser
   ```

4. **포트 충돌**
   ```bash
   # 포트 사용 확인
   lsof -i :6080
   lsof -i :5001
   ```

### 로그 확인

```bash
# 상세 로그
docker logs --tail 100 magentic-processgpt-browser

# 실시간 로그
docker logs -f magentic-processgpt-browser
```

## 📈 성능 최적화

### 브라우저 설정
- **헤드리스 모드**: 서버 환경에서 `BROWSER_HEADLESS=true` 설정
- **액션 제한**: `MAX_ACTIONS=20-50` 으로 제한하여 무한 루프 방지
- **타임아웃**: `TASK_TIMEOUT=60-120` 으로 적절한 시간 설정

### 리소스 관리
- **메모리**: Docker 실행 시 `--shm-size=2gb` 권장
- **CPU**: 브라우저 자동화는 CPU 집약적이므로 충분한 리소스 할당

## 🔐 보안 고려사항

1. **API 키 보호**: 환경변수로만 관리, 코드에 하드코딩 금지
2. **네트워크 격리**: Docker 네트워크 사용으로 격리
3. **권한 제한**: 컨테이너 내 최소 권한으로 실행
4. **로그 보안**: API 키가 로그에 노출되지 않도록 마스킹

## 📞 지원 및 문의

- **로그 확인**: 오류 발생 시 로그를 먼저 확인
- **환경변수**: .env 파일의 모든 필수 변수 설정 확인
- **네트워크**: 방화벽 및 포트 개방 상태 확인

---

✅ **요약**: Docker 실행 시 `processgpt_browser_server_standalone.py`가 자동으로 시작되어 Google에서 'playwright' 검색 등의 브라우저 자동화 작업을 수행합니다.
