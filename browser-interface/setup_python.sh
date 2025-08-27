#!/bin/bash

# Python 환경 설정 및 browser-use 설치 스크립트

set -e

echo "🐍 Python 환경 설정 및 browser-use 설치"
echo "========================================"

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

# 1. Python 버전 확인
print_info "Python 버전 확인 중..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3이 설치되지 않았습니다. Python 3.8 이상을 설치해주세요."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
print_success "Python $PYTHON_VERSION 확인됨"

# 2. pip 확인
print_info "pip 확인 중..."
if ! command -v pip3 &> /dev/null; then
    print_error "pip3이 설치되지 않았습니다."
    exit 1
fi

print_success "pip3 확인됨"

# 3. 가상환경 생성 또는 활성화
print_info "Python 가상환경 설정 중..."
if [ ! -d "venv" ]; then
    print_info "가상환경을 생성합니다..."
    python3 -m venv venv
    print_success "가상환경 생성 완료"
fi

# 가상환경 활성화
source venv/bin/activate
print_success "가상환경 활성화됨"

# 4. 필요한 패키지 설치
print_info "Python 패키지 설치 중..."
pip install --upgrade pip

# requirements.txt가 있으면 사용, 없으면 직접 설치
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    print_info "requirements.txt가 없습니다. 직접 패키지를 설치합니다..."
    pip install browser-use flask flask-cors playwright nest-asyncio
fi

print_success "Python 패키지 설치 완료"

# 5. OpenAI API 키 확인
print_info "OpenAI API 키 확인 중..."
if [ -z "$OPENAI_API_KEY" ]; then
    print_warning "OPENAI_API_KEY 환경변수가 설정되지 않았습니다."
    print_info "browser-use를 사용하려면 OpenAI API 키가 필요합니다."
    print_info "다음 중 하나의 방법으로 설정하세요:"
    print_info "1. export OPENAI_API_KEY='your-api-key-here'"
    print_info "2. .env 파일에 OPENAI_API_KEY=your-api-key-here 추가"
    print_info "3. 브라우저 서버 실행 시 환경변수로 전달"
else
    print_success "OpenAI API 키 확인됨"
fi

# 6. .env 파일 생성 (없는 경우)
if [ ! -f ".env" ]; then
    print_info ".env 파일을 생성합니다..."
    cat > .env << EOF
# OpenAI API 키 (browser-use에서 사용)
# OPENAI_API_KEY=your-api-key-here

# Flask 설정
FLASK_ENV=development
FLASK_DEBUG=True

# Playwright 설정
PLAYWRIGHT_WS_URL=ws://localhost:37367/default
EOF
    print_success ".env 파일 생성 완료"
    print_warning "⚠️  .env 파일에 OPENAI_API_KEY를 설정해주세요!"
fi

# 7. 테스트 실행
print_info "설치 테스트 중..."
if python3 -c "import browser_use; import flask; import playwright; print('모든 패키지가 정상적으로 설치되었습니다.')"; then
    print_success "패키지 설치 검증 완료"
else
    print_error "패키지 설치에 문제가 있습니다."
    exit 1
fi

echo ""
echo "🎉 Python 환경 설정 완료!"
echo "========================================"
print_success "가상환경: $(pwd)/venv"
print_success "Python 버전: $PYTHON_VERSION"
print_success "설치된 패키지: browser-use, flask, flask-cors, playwright, nest-asyncio"

echo ""
echo "📋 다음 단계:"
echo "1. OpenAI API 키 설정: export OPENAI_API_KEY='your-key' 또는 .env 파일 수정"
echo "2. Python 서버 시작: source venv/bin/activate && python browser_use_server.py"
echo "3. 웹 인터페이스에서 AI 기능 사용"

echo ""
print_info "가상환경 활성화 명령: source venv/bin/activate"
print_info "서버 시작 명령: python browser_use_server.py"
