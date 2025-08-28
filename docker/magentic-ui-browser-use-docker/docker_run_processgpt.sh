#!/bin/bash
# ProcessGPT Browser Server Docker 실행 스크립트

set -e

echo "🐳 ProcessGPT Browser Server Docker 실행"
echo "========================================"

# 현재 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "❌ .env 파일이 없습니다."
    echo "env.example을 참고하여 .env 파일을 생성하세요."
    exit 1
fi

# 환경변수 로드
source .env

# 필수 환경변수 확인
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다."
    exit 1
fi

echo "✅ 환경변수 확인 완료"

# Docker 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker build -t magentic-ui-processgpt-browser:latest .

if [ $? -ne 0 ]; then
    echo "❌ Docker 이미지 빌드 실패"
    exit 1
fi

echo "✅ Docker 이미지 빌드 완료"

# 기존 컨테이너 중지 및 제거
CONTAINER_NAME="magentic-processgpt-browser"
echo "🧹 기존 컨테이너 정리 중..."
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true

# 로그 디렉토리 생성
mkdir -p ./logs ./recordings

# Docker 컨테이너 실행
echo "🚀 Docker 컨테이너 실행 중..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -p 6080:6080 \
    -p 37367:37367 \
    -p 5001:5001 \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    -e SUPABASE_URL="${SUPABASE_URL:-}" \
    -e SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY:-}" \
    -e LLM_MODEL="${LLM_MODEL:-gpt-4o-mini}" \
    -e BROWSER_HEADLESS="${BROWSER_HEADLESS:-false}" \
    -e MAX_ACTIONS="${MAX_ACTIONS:-50}" \
    -e TASK_TIMEOUT="${TASK_TIMEOUT:-120}" \
    -e POLLING_INTERVAL="${POLLING_INTERVAL:-5}" \
    -e AGENT_ORCH="${AGENT_ORCH:-browser_automation_agent}" \
    -v "$(pwd)/recordings:/app/recordings" \
    -v "$(pwd)/logs:/app/logs" \
    --shm-size=2gb \
    magentic-ui-processgpt-browser:latest

if [ $? -ne 0 ]; then
    echo "❌ Docker 컨테이너 실행 실패"
    exit 1
fi

echo "✅ Docker 컨테이너 실행 완료"
echo ""
echo "📋 컨테이너 정보:"
echo "   이름: $CONTAINER_NAME"
echo "   포트:"
echo "     - 6080: noVNC (브라우저 화면 확인)"
echo "     - 37367: Playwright 서버"
echo "     - 5001: Browser-Use API 서버"
echo ""
echo "🌐 접속 URL:"
echo "   - noVNC: http://localhost:6080"
echo "   - API 헬스체크: http://localhost:5001/health"
echo ""
echo "📊 컨테이너 상태 확인:"
echo "   docker logs -f $CONTAINER_NAME"
echo ""
echo "🛑 컨테이너 중지:"
echo "   docker stop $CONTAINER_NAME"
echo ""
echo "🔄 컨테이너 재시작:"
echo "   docker restart $CONTAINER_NAME"
echo ""

# 컨테이너 시작 대기
echo "⏳ 컨테이너 시작 대기 (30초)..."
sleep 30

# 헬스 체크
echo "🏥 헬스 체크 수행 중..."
HEALTH_CHECK_URL="http://localhost:5001/health"

for i in {1..6}; do
    if curl -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
        echo "✅ 서버가 정상적으로 시작되었습니다!"
        echo "📊 상태 확인: curl $HEALTH_CHECK_URL"
        break
    else
        echo "⏳ 서버 시작 대기 중... ($i/6)"
        sleep 10
    fi
done

# 실시간 로그 표시 옵션
echo ""
echo "📄 실시간 로그를 보시겠습니까? (y/N)"
read -r SHOW_LOGS
if [[ "$SHOW_LOGS" =~ ^[Yy]$ ]]; then
    echo "📄 실시간 로그 표시 (Ctrl+C로 종료):"
    docker logs -f "$CONTAINER_NAME"
else
    echo "💡 로그 확인 방법:"
    echo "   docker logs -f $CONTAINER_NAME"
fi

echo ""
echo "🎉 ProcessGPT Browser Server Docker 실행 완료!"
