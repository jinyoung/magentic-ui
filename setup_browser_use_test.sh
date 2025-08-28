#!/bin/bash
# Browser-Use Agent 테스트 환경 설정 스크립트

echo "🚀 Browser-Use Agent 테스트 환경 설정 시작"
echo "================================================"

# Python 가상환경 확인
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  가상환경이 활성화되지 않았습니다."
    echo "다음 명령어로 가상환경을 생성하고 활성화하세요:"
    echo "python -m venv venv"
    echo "source venv/bin/activate  # Linux/macOS"
    echo "venv\\Scripts\\activate     # Windows"
    exit 1
fi

echo "✅ 가상환경 활성화됨: $VIRTUAL_ENV"

# 필수 패키지 설치
echo "📦 필수 패키지 설치 중..."
pip install -r requirements_browser_use_test.txt

# browser-use 설치
echo "🌐 browser-use 패키지 설치 중..."
pip install browser-use

# Playwright 브라우저 설치
echo "🎭 Playwright 브라우저 설치 중..."
playwright install chromium
playwright install-deps

# 환경변수 확인
echo "🔑 환경변수 확인..."
if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "⚠️  OPENAI_API_KEY 환경변수가 설정되지 않았습니다."
    echo "다음과 같이 설정하세요:"
    echo "export OPENAI_API_KEY='your-api-key-here'"
    echo ""
    echo "또는 .env 파일을 생성하세요:"
    echo "echo 'OPENAI_API_KEY=your-api-key-here' > .env"
else
    echo "✅ OPENAI_API_KEY 설정됨"
fi

# 디렉토리 생성
echo "📁 작업 디렉토리 생성..."
mkdir -p test_recording
mkdir -p logs

echo ""
echo "✅ 설정 완료!"
echo ""
echo "다음 명령어로 테스트를 실행하세요:"
echo "python run_browser_use_test.py"
echo ""
echo "또는 전체 테스트 스위트 실행:"
echo "python test_browser_use_agent.py"
