#!/bin/bash

# Magentic UI Browser with AI Control - 통합 시작 스크립트

set -e

echo "🚀 Magentic UI Browser with AI Control"
echo "======================================"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 현재 디렉토리로 이동
cd "$(dirname "$0")"

# 함수 정의
cleanup() {
    echo ""
    print_info "서비스들을 종료합니다..."
    
    # Python 서버 종료
    if [ ! -z "$PYTHON_PID" ]; then
        kill $PYTHON_PID 2>/dev/null || true
        print_info "Python AI 서버 종료됨"
    fi
    
    # Node.js 서버 종료
    if [ ! -z "$NODE_PID" ]; then
        kill $NODE_PID 2>/dev/null || true
        print_info "Node.js 웹 서버 종료됨"
    fi
    
    # Docker 컨테이너 종료 (선택사항)
    read -p "Docker 컨테이너도 종료하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker stop magentic-ui-browser 2>/dev/null || true
        print_info "Docker 컨테이너 종료됨"
    fi
    
    print_success "모든 서비스가 종료되었습니다"
    exit 0
}

# Ctrl+C 시그널 처리
trap cleanup SIGINT SIGTERM

# 1. 시스템 요구사항 확인
print_info "시스템 요구사항 확인 중..."

# Node.js 확인
if ! command -v node &> /dev/null; then
    print_error "Node.js가 설치되지 않았습니다."
    exit 1
fi

# Python 확인
if ! command -v python3 &> /dev/null; then
    print_error "Python 3가 설치되지 않았습니다."
    exit 1
fi

# Docker 확인
if ! command -v docker &> /dev/null; then
    print_error "Docker가 설치되지 않았습니다."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker가 실행되지 않았습니다."
    exit 1
fi

print_success "시스템 요구사항 확인 완료"

# 2. Python 환경 설정
print_info "Python 환경 확인 중..."
if [ ! -d "venv" ]; then
    print_warning "Python 가상환경이 없습니다. 자동으로 설정합니다..."
    ./setup_python.sh
fi

print_success "Python 환경 준비됨"

# 3. Node.js 의존성 확인
print_info "Node.js 의존성 확인 중..."
if [ ! -d "node_modules" ]; then
    print_info "Node.js 의존성을 설치합니다..."
    npm install
fi

print_success "Node.js 의존성 준비됨"

# 4. Docker 이미지 확인
print_info "Docker 이미지 확인 중..."
if ! docker images | grep -q "magentic-ui-browser.*latest"; then
    print_info "Docker 이미지를 빌드합니다..."
    npm run build-image
fi

print_success "Docker 이미지 준비됨"

# 5. Docker 컨테이너 시작
print_info "Docker 컨테이너 상태 확인 중..."
if ! docker ps | grep -q "magentic-ui-browser"; then
    print_info "Docker 컨테이너를 시작합니다..."
    
    # 기존 컨테이너 정리
    docker stop magentic-ui-browser 2>/dev/null || true
    docker rm magentic-ui-browser 2>/dev/null || true
    
    # 새 컨테이너 시작
    docker run -d --name magentic-ui-browser \
        -p 6080:6080 \
        -p 37367:37367 \
        magentic-ui-browser:latest
    
    print_info "컨테이너 시작 대기 중..."
    sleep 10
fi

print_success "Docker 컨테이너 실행 중"

# 6. Python AI 서버 시작
print_info "Python AI 서버 시작 중..."

# 가상환경 활성화 확인
if [ ! -f "venv/bin/activate" ]; then
    print_error "Python 가상환경을 찾을 수 없습니다. setup_python.sh를 먼저 실행하세요."
    exit 1
fi

# Python 서버를 백그라운드에서 시작
(
    source venv/bin/activate
    echo "🤖 Browser-Use AI 서버 시작 중..."
    python browser_use_server.py
) &

PYTHON_PID=$!
print_success "Python AI 서버 시작됨 (PID: $PYTHON_PID)"

# Python 서버 시작 대기
print_info "AI 서버 초기화 대기 중..."
sleep 5

# 7. Node.js 웹 서버 시작
print_info "Node.js 웹 서버 시작 중..."

# 기존 서버 종료
pkill -f "node docker-manager.js" 2>/dev/null || true

# 웹 서버를 백그라운드에서 시작
node docker-manager.js &
NODE_PID=$!

print_success "Node.js 웹 서버 시작됨 (PID: $NODE_PID)"

# 웹 서버 시작 대기
print_info "웹 서버 초기화 대기 중..."
sleep 3

# 8. 서비스 상태 확인
print_info "서비스 상태 확인 중..."

# 웹 서버 확인
if curl -s http://localhost:3000 > /dev/null; then
    print_success "웹 서버: http://localhost:3000 ✅"
else
    print_error "웹 서버 연결 실패"
fi

# VNC 서버 확인
if curl -s http://localhost:6080 > /dev/null; then
    print_success "VNC 서버: http://localhost:6080 ✅"
else
    print_warning "VNC 서버 연결 실패"
fi

# AI 서버 확인
if curl -s http://localhost:5000/health > /dev/null; then
    print_success "AI 서버: http://localhost:5000 ✅"
else
    print_warning "AI 서버 연결 실패"
fi

# 9. 사용 안내
echo ""
echo "🎉 모든 서비스가 시작되었습니다!"
echo "=================================="
print_success "웹 인터페이스: http://localhost:3000"
print_success "VNC 직접 접속: http://localhost:6080"
print_success "AI 서버 API: http://localhost:5000"

echo ""
echo "📋 사용 방법:"
echo "1. 브라우저에서 http://localhost:3000 접속"
echo "2. '컨테이너 시작' 버튼 클릭 (이미 실행 중)"
echo "3. '브라우저 시작' 버튼으로 기본 브라우저 실행"
echo "4. AI 제어 패널에서 자연어 명령 입력"
echo ""
echo "🤖 AI 명령 예시:"
echo "- 'Google에서 Playwright 검색하기'"
echo "- '첫 번째 검색 결과 클릭하기'"
echo "- '페이지 맨 아래로 스크롤하기'"

echo ""
print_info "서비스들이 백그라운드에서 실행 중입니다."
print_info "Ctrl+C를 눌러서 모든 서비스를 종료할 수 있습니다."

# OpenAI API 키 확인
if [ -z "$OPENAI_API_KEY" ]; then
    echo ""
    print_warning "⚠️  OpenAI API 키가 설정되지 않았습니다!"
    print_info "AI 기능을 사용하려면 다음 중 하나를 수행하세요:"
    print_info "1. export OPENAI_API_KEY='your-api-key'"
    print_info "2. .env 파일에 OPENAI_API_KEY=your-key 추가"
    print_info "3. 서버 재시작"
fi

echo ""
print_info "웹 브라우저를 자동으로 열고 있습니다..."

# 브라우저 자동 열기 (macOS)
if command -v open &> /dev/null; then
    sleep 2
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    sleep 2
    xdg-open http://localhost:3000
fi

# 서버들이 종료될 때까지 대기
wait
