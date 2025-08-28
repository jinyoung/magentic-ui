#!/bin/bash

echo "🚀 Browser Control UI 데모 시작 스크립트"
echo "========================================="

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 포트 확인 함수
check_port() {
    local port=$1
    local service=$2
    
    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "✅ 포트 $port ($service) 사용 중"
        return 0
    else
        echo -e "❌ 포트 $port ($service) 사용 불가"
        return 1
    fi
}

echo ""
echo "📋 1. 시스템 요구사항 확인..."

# Node.js 버전 확인
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js 설치됨: $NODE_VERSION${NC}"
else
    echo -e "${RED}❌ Node.js가 설치되지 않았습니다${NC}"
    exit 1
fi

# npm 확인
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✅ npm 설치됨: $NPM_VERSION${NC}"
else
    echo -e "${RED}❌ npm이 설치되지 않았습니다${NC}"
    exit 1
fi

echo ""
echo "📋 2. 백엔드 서비스 상태 확인..."

# Docker 확인
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker 설치됨${NC}"
    
    # Docker 컨테이너 확인
    if docker ps | grep -q "magentic-ui-browser-use"; then
        echo -e "${GREEN}✅ Browser-Use 컨테이너 실행 중${NC}"
    else
        echo -e "${YELLOW}⚠️ Browser-Use 컨테이너가 실행되지 않았습니다${NC}"
        echo "다음 명령어로 컨테이너를 시작하세요:"
        echo "cd ../docker/magentic-ui-browser-use-docker && ./quick-build.sh"
    fi
else
    echo -e "${YELLOW}⚠️ Docker가 설치되지 않았습니다${NC}"
fi

# 백엔드 API 포트 확인
echo ""
echo "📋 3. API 서비스 확인..."

# Browser-Use API (포트 5001)
if curl -s http://localhost:5001/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Browser-Use API (포트 5001) 응답 정상${NC}"
else
    echo -e "${YELLOW}⚠️ Browser-Use API (포트 5001) 응답 없음${NC}"
fi

# Docker Manager (포트 3000)
if curl -s http://localhost:3000/api/status >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker Manager (포트 3000) 응답 정상${NC}"
else
    echo -e "${YELLOW}⚠️ Docker Manager (포트 3000) 응답 없음${NC}"
fi

# VNC (포트 6080)
if curl -s http://localhost:6080 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ VNC 서비스 (포트 6080) 응답 정상${NC}"
else
    echo -e "${YELLOW}⚠️ VNC 서비스 (포트 6080) 응답 없음${NC}"
fi

echo ""
echo "📋 4. 프론트엔드 의존성 확인..."

# package.json 확인
if [ -f "package.json" ]; then
    echo -e "${GREEN}✅ package.json 존재${NC}"
else
    echo -e "${RED}❌ package.json이 없습니다${NC}"
    exit 1
fi

# node_modules 확인
if [ -d "node_modules" ]; then
    echo -e "${GREEN}✅ 의존성 설치됨${NC}"
else
    echo -e "${YELLOW}⚠️ 의존성 설치 필요${NC}"
    echo "npm install을 실행합니다..."
    npm install
fi

echo ""
echo "🚀 5. 개발 서버 시작..."

# 포트 5173 확인
if lsof -i :5173 >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ 포트 5173이 이미 사용 중입니다${NC}"
    echo "기존 프로세스를 종료하고 다시 시작하시겠습니까? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "기존 프로세스를 종료합니다..."
        pkill -f "vite.*5173" || true
        sleep 2
    else
        echo "종료합니다."
        exit 0
    fi
fi

echo ""
echo -e "${GREEN}🎉 모든 준비가 완료되었습니다!${NC}"
echo ""
echo "📱 접속 정보:"
echo "  웹 UI:        http://localhost:5173"
echo "  VNC 뷰어:     http://localhost:6080"
echo "  Browser-Use:  http://localhost:5001"
echo "  Docker Mgr:   http://localhost:3000"
echo ""
echo "🔧 사용법:"
echo "  1. 웹 브라우저에서 http://localhost:5173 접속"
echo "  2. 우측 VNC 패널에서 브라우저 화면 확인"
echo "  3. 좌측 패널에서 자연어 태스크 입력 및 실행"
echo ""
echo "⏰ 개발 서버를 시작합니다... (Ctrl+C로 종료)"
echo ""

# 개발 서버 시작
npm run dev
