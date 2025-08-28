# ProcessGPT Browser Automation Full Stack

Supabase를 포함한 완전한 ProcessGPT 브라우저 자동화 스택입니다. Docker Compose를 사용하여 한 번에 모든 서비스를 실행하고 테스트할 수 있습니다.

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Supabase      │    │  ProcessGPT     │    │   Browser       │
│   (PostgreSQL)  │◄──►│  Browser Server │◄──►│   Automation    │
│                 │    │                 │    │   (browser-use) │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • PostgreSQL    │    │ • Task Polling  │    │ • Playwright    │
│ • PostgREST     │    │ • AgentExecutor │    │ • Chromium      │
│ • GoTrue (Auth) │    │ • Event Logging │    │ • noVNC View    │
│ • Kong Gateway  │    │ • Status Update │    │ • Recording     │
│ • Studio UI     │    │ • Error Handle  │    │ • Screenshots   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 빠른 시작

### 1. 전체 스택 실행

```bash
# OpenAI API 키가 .env에 설정되어 있는지 확인
cat .env

# 전체 스택 실행 (자동화 스크립트)
./run_full_stack.sh

# 또는 수동 실행
docker-compose up --build -d
```

### 2. 서비스 확인

실행 후 다음 서비스들이 시작됩니다:

| 서비스 | 포트 | 설명 | URL |
|--------|------|------|-----|
| **Supabase Studio** | 3001 | 데이터베이스 관리 UI | http://localhost:3001 |
| **Supabase API** | 54321 | REST API 엔드포인트 | http://localhost:54321 |
| **PostgreSQL** | 5432 | 데이터베이스 | localhost:5432 |
| **Browser noVNC** | 6080 | 브라우저 화면 확인 | http://localhost:6080 |
| **Browser API** | 5001 | Browser-Use API | http://localhost:5001 |
| **Playwright** | 37367 | Playwright 서버 | localhost:37367 |

### 3. 테스트 실행

```bash
# 풀스택 테스트 실행
python3 test_full_stack.py

# 또는 실행 스크립트에서 선택
./run_full_stack.sh
# → 'y' 선택하여 테스트 실행
```

## 📊 Supabase 데이터베이스

### 테이블 구조

#### `todolist` - 작업 관리
```sql
CREATE TABLE todolist (
    id UUID PRIMARY KEY,
    activity_name TEXT NOT NULL,
    description TEXT NOT NULL,
    status todo_status DEFAULT 'PENDING',
    agent_orch agent_orch DEFAULT 'browser_automation_agent',
    user_id TEXT DEFAULT 'system',
    output JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `events` - 이벤트 로깅
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY,
    todolist_id UUID REFERENCES todolist(id),
    event_type VARCHAR(50),
    event_data JSONB,
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 초기 테스트 데이터

시스템 시작 시 다음 테스트 작업들이 자동으로 생성됩니다:

1. **Google Playwright 검색**
   ```json
   {
     "description": "Google에서 'playwright' 검색하고 첫 번째 결과 클릭하기",
     "status": "PENDING",
     "agent_orch": "browser_automation_agent"
   }
   ```

2. **GitHub 홈페이지 방문**
   ```json
   {
     "description": "GitHub 홈페이지로 이동하고 주요 정보 수집하기",
     "status": "PENDING",
     "agent_orch": "browser_automation_agent"
   }
   ```

3. **네이버 날씨 검색**
   ```json
   {
     "description": "네이버에서 '날씨' 검색하고 현재 날씨 정보 가져오기",
     "status": "PENDING",
     "agent_orch": "browser_automation_agent"
   }
   ```

## 🔄 작업 처리 플로우

### 1. 작업 생성
```sql
-- 새로운 브라우저 작업 추가
INSERT INTO todolist (activity_name, description, agent_orch, status)
VALUES ('custom_task', 'Stack Overflow에서 Python 질문 검색하기', 'browser_automation_agent', 'PENDING');
```

### 2. 자동 처리
- ProcessGPT 서버가 10초마다 `PENDING` 상태의 작업을 폴링
- 발견된 작업을 `IN_PROGRESS`로 상태 변경
- Browser-Use AgentExecutor를 통해 작업 실행
- 실행 과정의 이벤트들을 `events` 테이블에 로깅
- 완료 시 `DONE` 또는 실패 시 `CANCELLED`로 상태 업데이트

### 3. 실시간 모니터링
- **Supabase Studio**: 데이터베이스 상태 실시간 확인
- **noVNC**: 브라우저 자동화 과정 시각적 확인
- **로그**: Docker Compose 로그로 상세한 실행 과정 추적

## 🧪 테스트 시나리오

### 자동 테스트 스위트

`test_full_stack.py`가 다음 테스트들을 수행합니다:

1. **서비스 연결성 테스트**
   - Supabase API 연결
   - PostgreSQL 연결
   - Browser API 연결

2. **데이터베이스 CRUD 테스트**
   - 작업 조회 (SELECT)
   - 작업 생성 (INSERT)
   - 작업 업데이트 (UPDATE)

3. **End-to-End 워크플로우 테스트**
   - 테스트 작업 생성
   - 자동 처리 대기 (최대 2분)
   - 결과 확인 및 검증

4. **이벤트 로깅 테스트**
   - 실행 이벤트 기록 확인
   - 로그 데이터 무결성 검증

### 수동 테스트

```bash
# 1. Supabase Studio에서 직접 작업 추가
# http://localhost:3001 접속 → todolist 테이블 → Insert row

# 2. 브라우저 화면으로 실행 과정 확인
# http://localhost:6080 접속 → 브라우저 자동화 과정 실시간 관찰

# 3. API를 통한 직접 작업 실행
curl -X POST http://localhost:5001/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "Google에서 \"browser automation\" 검색하기"}'
```

## 🛠️ 개발 및 디버깅

### 로그 확인

```bash
# 전체 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f processgpt-browser
docker-compose logs -f postgres
docker-compose logs -f kong

# 실시간 로그 (최근 100라인)
docker-compose logs --tail=100 -f processgpt-browser
```

### 데이터베이스 직접 접속

```bash
# PostgreSQL 컨테이너 접속
docker-compose exec postgres psql -U postgres -d postgres

# 작업 상태 확인
SELECT id, activity_name, status, created_at FROM todolist ORDER BY created_at DESC LIMIT 10;

# 이벤트 로그 확인
SELECT event_type, message, created_at FROM events ORDER BY created_at DESC LIMIT 10;
```

### 컨테이너 내부 디버깅

```bash
# ProcessGPT 브라우저 서버 컨테이너 접속
docker-compose exec processgpt-browser bash

# 수동으로 서버 실행 (디버깅용)
docker-compose exec processgpt-browser python3 /app/processgpt_browser_server_supabase.py
```

## 🔧 설정 커스터마이징

### 환경변수 수정

`.env` 파일에서 설정을 변경할 수 있습니다:

```bash
# 브라우저 설정
BROWSER_HEADLESS=true          # GUI 없이 실행
MAX_ACTIONS=20                 # 액션 수 제한
TASK_TIMEOUT=180              # 3분 타임아웃

# 폴링 설정
POLLING_INTERVAL=5            # 5초마다 폴링
AGENT_ORCH=web_scraping_agent # 다른 에이전트 타입

# LLM 설정
LLM_MODEL=gpt-4               # 더 강력한 모델 사용
```

### Docker Compose 커스터마이징

`docker-compose.yml`에서 서비스 설정을 변경할 수 있습니다:

```yaml
# 메모리 제한 추가
processgpt-browser:
  # ...
  deploy:
    resources:
      limits:
        memory: 4G
      reservations:
        memory: 2G

# 포트 변경
ports:
  - "8080:6080"   # noVNC 포트 변경
  - "9001:5001"   # API 포트 변경
```

## 🚨 문제 해결

### 일반적인 문제들

1. **서비스 시작 실패**
   ```bash
   # 포트 충돌 확인
   lsof -i :5432 -i :54321 -i :6080 -i :5001
   
   # 기존 컨테이너 정리
   docker-compose down -v
   docker system prune -f
   ```

2. **Supabase 연결 실패**
   ```bash
   # Supabase 서비스 상태 확인
   docker-compose ps | grep -E "(postgres|kong|postgrest)"
   
   # 데이터베이스 로그 확인
   docker-compose logs postgres
   ```

3. **브라우저 실행 오류**
   ```bash
   # ProcessGPT 서버 로그 확인
   docker-compose logs processgpt-browser
   
   # 환경변수 확인
   docker-compose exec processgpt-browser env | grep -E "(OPENAI|DISPLAY)"
   ```

4. **작업이 처리되지 않음**
   ```sql
   -- 데이터베이스에서 작업 상태 확인
   SELECT * FROM todolist WHERE status = 'PENDING';
   
   -- 이벤트 로그 확인
   SELECT * FROM events ORDER BY created_at DESC LIMIT 5;
   ```

### 성능 최적화

1. **메모리 부족**
   ```bash
   # Docker에 더 많은 메모리 할당
   docker-compose.yml에서 shm_size 증가
   ```

2. **느린 작업 처리**
   ```bash
   # 폴링 간격 단축
   POLLING_INTERVAL=5
   
   # 더 강력한 LLM 모델 사용
   LLM_MODEL=gpt-4
   ```

## 📈 모니터링 및 운영

### 헬스 체크

```bash
# 전체 시스템 상태 확인
curl http://localhost:5001/health
curl http://localhost:54321/rest/v1/rpc/health_check \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 메트릭 수집

```sql
-- 작업 처리 통계
SELECT 
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (end_date - start_date))) as avg_duration_seconds
FROM todolist 
WHERE start_date IS NOT NULL
GROUP BY status;

-- 에이전트별 성공률
SELECT 
    agent_orch,
    COUNT(*) as total,
    COUNT(CASE WHEN status = 'DONE' THEN 1 END) as successful,
    ROUND(COUNT(CASE WHEN status = 'DONE' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
FROM todolist
GROUP BY agent_orch;
```

## 🔒 보안 고려사항

1. **API 키 보호**: 프로덕션에서는 `.env` 파일을 git에 커밋하지 않음
2. **네트워크 격리**: Docker 네트워크 사용으로 서비스간 격리
3. **데이터베이스 접근**: RLS(Row Level Security) 정책 적용
4. **로그 마스킹**: API 키가 로그에 노출되지 않도록 처리

---

## ✅ 요약

**Docker Compose로 Supabase를 포함한 완전한 ProcessGPT 브라우저 자동화 스택이 구축되었습니다:**

- 🗄️ **Supabase**: PostgreSQL + REST API + 관리 UI
- 🤖 **ProcessGPT Server**: 작업 폴링 및 자동 실행
- 🌐 **Browser Automation**: browser-use를 통한 웹 자동화
- 🧪 **Full Stack Testing**: 완전한 E2E 테스트 스위트

**실행 명령**: `./run_full_stack.sh`
