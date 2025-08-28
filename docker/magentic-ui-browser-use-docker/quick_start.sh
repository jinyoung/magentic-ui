#!/bin/bash
# ProcessGPT Browser Automation Server 빠른 시작 스크립트

set -e  # 오류 발생 시 스크립트 중지

echo "🚀 ProcessGPT Browser Automation Server 빠른 시작"
echo "=================================================="

# 현재 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 작업 디렉토리: $SCRIPT_DIR"

# 1. Python 버전 확인
echo "🐍 Python 버전 확인..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3이 설치되지 않았습니다."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION 발견"

if [[ $(echo "$PYTHON_VERSION < 3.8" | bc -l 2>/dev/null || echo 0) == 1 ]]; then
    echo "❌ Python 3.8 이상이 필요합니다."
    exit 1
fi

# 2. 필수 패키지 설치
echo "📦 필수 패키지 설치 중..."

PACKAGES=(
    "browser-use"
    "playwright"
    "pydantic"
    "asyncio"
    "requests"
)

for package in "${PACKAGES[@]}"; do
    echo "  Installing $package..."
    pip3 install "$package" --quiet || {
        echo "❌ $package 설치 실패"
        exit 1
    }
done

echo "✅ 필수 패키지 설치 완료"

# 3. Playwright 브라우저 설치
echo "🎭 Playwright 브라우저 설치 중..."
playwright install chromium --quiet || {
    echo "❌ Playwright 브라우저 설치 실패"
    exit 1
}
echo "✅ Playwright 브라우저 설치 완료"

# 4. 환경변수 파일 확인
echo "🔑 환경변수 확인..."
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        echo "📋 환경변수 예시 파일에서 .env 생성..."
        cp env.example .env
        echo "⚠️  .env 파일을 편집하여 실제 값을 입력하세요:"
        echo "   - SUPABASE_URL"
        echo "   - SUPABASE_ANON_KEY"
        echo "   - OPENAI_API_KEY"
    else
        echo "❌ env.example 파일이 없습니다."
        exit 1
    fi
else
    echo "✅ .env 파일 발견"
fi

# 환경변수 로드
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 필수 환경변수 확인
REQUIRED_VARS=("OPENAI_API_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "❌ 다음 필수 환경변수가 설정되지 않았습니다:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo "💡 .env 파일을 편집하여 값을 설정하세요."
else
    echo "✅ 필수 환경변수 확인됨"
fi

# 5. 디렉토리 생성
echo "📁 작업 디렉토리 생성..."
mkdir -p recordings logs
echo "✅ 디렉토리 생성 완료"

# 6. 권한 설정
echo "🔧 실행 권한 설정..."
chmod +x *.py 2>/dev/null || true
echo "✅ 권한 설정 완료"

# 7. 테스트 실행 (선택사항)
echo ""
echo "🧪 통합 테스트를 실행하시겠습니까? (y/N)"
read -r RESPONSE
if [[ "$RESPONSE" =~ ^[Yy]$ ]]; then
    echo "🧪 통합 테스트 실행 중..."
    python3 test_processgpt_integration.py
else
    echo "⏭️  테스트 건너뜀"
fi

echo ""
echo "✅ 설정 완료!"
echo ""
echo "🎯 다음 단계:"
echo "1. .env 파일 편집 (필수 환경변수 설정)"
echo "2. ProcessGPT 서버 실행:"
echo "   python3 processgpt_browser_server.py"
echo ""
echo "3. 또는 통합 테스트:"
echo "   python3 test_processgpt_integration.py"
echo ""
echo "📚 추가 정보:"
echo "   - README_INTEGRATED.md: 자세한 사용법"
echo "   - env.example: 환경변수 설정 예시"
echo ""
echo "🆘 문제가 발생하면:"
echo "   - 로그 확인: 터미널 출력"
echo "   - 환경변수 재확인"
echo "   - Python 패키지 재설치"
