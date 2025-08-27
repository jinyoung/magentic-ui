#!/bin/bash

# Quick Start Script for Magentic UI Browser Interface

set -e

echo "🚀 Magentic UI Browser Interface Quick Start"
echo "============================================"

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
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

# 현재 디렉토리로 이동
cd "$(dirname "$0")"

# 1. 의존성 설치
if [ ! -d "node_modules" ]; then
    print_info "의존성 설치 중..."
    npm install
    print_success "의존성 설치 완료"
fi

# 2. Docker 이미지 확인/빌드
if ! docker images | grep -q "magentic-ui-browser.*latest"; then
    print_info "Docker 이미지 빌드 중..."
    npm run build-image
    print_success "Docker 이미지 빌드 완료"
else
    print_success "Docker 이미지 준비됨"
fi

# 3. 웹 서버 시작
print_info "웹 서버 시작 중..."
print_warning "웹 브라우저에서 http://localhost:3000 을 열어주세요"
print_warning "Ctrl+C를 눌러 서버를 종료할 수 있습니다"

echo ""
echo "======================================"
echo "🌐 웹 인터페이스: http://localhost:3000"
echo "🐳 Docker 이미지: magentic-ui-browser:latest"
echo "📱 noVNC 포트: 6080"
echo "🎭 Playwright 포트: 37367"
echo "======================================"
echo ""

npm start
