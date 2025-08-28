#!/bin/bash
# ProcessGPT Browser Automation Full Stack 실행 스크립트

set -e

echo "🚀 ProcessGPT Browser Automation Full Stack"
echo "============================================="

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

# Docker Compose 버전 확인
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose가 설치되지 않았습니다."
    exit 1
fi

echo "🐳 Docker Compose 버전: $(docker-compose --version)"

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리 중..."
docker-compose down -v 2>/dev/null || true

# 볼륨 및 네트워크 정리
echo "🧹 볼륨 및 네트워크 정리 중..."
docker volume prune -f 2>/dev/null || true
docker network prune -f 2>/dev/null || true

# 로그 디렉토리 생성
echo "📁 작업 디렉토리 생성..."
mkdir -p ./logs ./recordings

# Docker Compose 빌드 및 실행
echo "🔨 Docker Compose 빌드 및 실행 중..."
export OPENAI_API_KEY="$OPENAI_API_KEY"

# 백그라운드에서 모든 서비스 시작
docker-compose up --build -d

if [ $? -ne 0 ]; then
    echo "❌ Docker Compose 실행 실패"
    exit 1
fi

echo "✅ Docker Compose 실행 완료"
echo ""

# 서비스 상태 확인
echo "📊 서비스 상태 확인 중..."
sleep 5
docker-compose ps

echo ""
echo "🌐 서비스 접속 정보:"
echo "  📊 Supabase Studio: http://localhost:3001"
echo "  🌐 Browser noVNC: http://localhost:6080"
echo "  🔧 Browser API: http://localhost:5001"
echo "  🗄️  Supabase API: http://localhost:54321"
echo "  🗄️  PostgreSQL: localhost:5432"
echo ""

# 서비스 준비 대기
echo "⏳ 서비스 준비 대기 중 (60초)..."
sleep 60

# 헬스 체크
echo "🏥 서비스 헬스 체크 수행 중..."

# Supabase API 체크
SUPABASE_URL="http://localhost:54321/rest/v1/"
echo "  - Supabase API 체크..."
if curl -s "$SUPABASE_URL" > /dev/null 2>&1; then
    echo "    ✅ Supabase API 응답"
else
    echo "    ⚠️ Supabase API 응답 없음"
fi

# Browser API 체크
BROWSER_URL="http://localhost:5001/health"
echo "  - Browser API 체크..."
if curl -s "$BROWSER_URL" > /dev/null 2>&1; then
    echo "    ✅ Browser API 응답"
else
    echo "    ⚠️ Browser API 응답 없음"
fi

echo ""
echo "🧪 풀스택 테스트를 실행하시겠습니까? (y/N)"
read -r RUN_TEST
if [[ "$RUN_TEST" =~ ^[Yy]$ ]]; then
    echo "🧪 풀스택 테스트 실행 중..."
    
    # aiohttp 설치 확인
    if ! python3 -c "import aiohttp" 2>/dev/null; then
        echo "📦 aiohttp 설치 중..."
        pip3 install aiohttp
    fi
    
    python3 test_full_stack.py
else
    echo "⏭️  테스트 건너뜀"
fi

echo ""
echo "📄 실시간 로그를 보시겠습니까? (y/N)"
read -r SHOW_LOGS
if [[ "$SHOW_LOGS" =~ ^[Yy]$ ]]; then
    echo "📄 실시간 로그 표시 (Ctrl+C로 종료):"
    docker-compose logs -f processgpt-browser
else
    echo "💡 로그 확인 방법:"
    echo "  docker-compose logs -f                    # 모든 서비스"
    echo "  docker-compose logs -f processgpt-browser # 브라우저 서버만"
    echo "  docker-compose logs -f postgres           # PostgreSQL만"
fi

echo ""
echo "🛑 전체 스택을 중지하려면:"
echo "  docker-compose down"
echo ""
echo "🔄 서비스를 재시작하려면:"
echo "  docker-compose restart"
echo ""
echo "🧹 완전히 정리하려면:"
echo "  docker-compose down -v"
echo "  docker system prune -f"
echo ""
echo "🎉 ProcessGPT Browser Automation Full Stack 실행 완료!"
