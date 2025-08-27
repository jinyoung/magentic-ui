#!/bin/bash

# Magentic UI Browser Interface 시작 스크립트

set -e

echo "🚀 Magentic UI Browser Interface 시작 중..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
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

# 스크립트 디렉토리로 이동
cd "$(dirname "$0")"

# 1. Node.js 버전 확인
print_info "Node.js 버전 확인 중..."
if ! command -v node &> /dev/null; then
    print_error "Node.js가 설치되지 않았습니다. Node.js 16.0.0 이상을 설치해주세요."
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2)
REQUIRED_VERSION="16.0.0"

if ! node -e "process.exit(require('semver').gte('$NODE_VERSION', '$REQUIRED_VERSION') ? 0 : 1)" 2>/dev/null; then
    print_warning "Node.js 버전이 낮을 수 있습니다. 현재: v$NODE_VERSION, 권장: v$REQUIRED_VERSION 이상"
fi

print_success "Node.js v$NODE_VERSION 확인됨"

# 2. Docker 설치 및 실행 상태 확인
print_info "Docker 상태 확인 중..."
if ! command -v docker &> /dev/null; then
    print_error "Docker가 설치되지 않았습니다. Docker를 설치해주세요."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker가 실행되지 않았습니다. Docker를 시작해주세요."
    exit 1
fi

print_success "Docker 확인됨"

# 3. 의존성 설치 확인
print_info "의존성 확인 중..."
if [ ! -d "node_modules" ]; then
    print_info "의존성을 설치합니다..."
    npm install
    print_success "의존성 설치 완료"
else
    print_success "의존성이 이미 설치되어 있습니다"
fi

# 4. Docker 이미지 존재 확인
print_info "Docker 이미지 확인 중..."
if ! docker images | grep -q "magentic-ui-browser.*latest"; then
    print_warning "Docker 이미지가 없습니다. 이미지를 빌드하시겠습니까? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_info "Docker 이미지 빌드 중... (몇 분이 소요될 수 있습니다)"
        npm run build-image
        print_success "Docker 이미지 빌드 완료"
    else
        print_warning "Docker 이미지 없이 계속합니다. 웹 인터페이스에서 빌드할 수 있습니다."
    fi
else
    print_success "Docker 이미지 확인됨"
fi

# 5. 포트 사용 확인
print_info "포트 사용 상태 확인 중..."
SERVER_PORT=${PORT:-3000}
VNC_PORT=6080
PLAYWRIGHT_PORT=37367

check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "$service 포트 $port가 이미 사용 중입니다"
        return 1
    fi
    return 0
}

check_port $SERVER_PORT "웹 서버"
check_port $VNC_PORT "noVNC"
check_port $PLAYWRIGHT_PORT "Playwright"

# 6. 웹 서버 시작
print_info "웹 서버를 포트 $SERVER_PORT에서 시작합니다..."

# 개발 모드 또는 프로덕션 모드 선택
if [ "$1" = "--dev" ] || [ "$NODE_ENV" = "development" ]; then
    print_info "개발 모드로 시작합니다 (nodemon 사용)"
    if command -v nodemon &> /dev/null; then
        npm run dev
    else
        print_warning "nodemon이 설치되지 않았습니다. 일반 모드로 시작합니다."
        npm start
    fi
else
    print_info "프로덕션 모드로 시작합니다"
    npm start
fi
