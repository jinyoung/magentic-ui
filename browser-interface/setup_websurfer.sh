#!/bin/bash

# Magentic UI WebSurfer Server 설정 스크립트

echo "🤖 Magentic UI WebSurfer Server 설정 시작..."

# Python 가상환경 생성
echo "📦 Python 가상환경 생성 중..."
python3 -m venv venv_websurfer

# 가상환경 활성화
echo "🔥 가상환경 활성화 중..."
source venv_websurfer/bin/activate

# 의존성 설치
echo "📚 패키지 설치 중..."
pip install --upgrade pip
pip install -r requirements_websurfer.txt

# Playwright 브라우저 설치
echo "🌐 Playwright 브라우저 설치 중..."
playwright install chromium

# .env 파일 생성 (존재하지 않는 경우)
if [ ! -f .env ]; then
    echo "⚙️ .env 파일 생성 중..."
    cat > .env << EOL
# OpenAI API 키 (필수)
OPENAI_API_KEY=your-openai-api-key-here

# 서버 설정
WEBSURFER_PORT=5002
WEBSURFER_HOST=0.0.0.0

# Playwright 설정
PLAYWRIGHT_WS_URL=ws://localhost:37367/default
EOL
    echo "📝 .env 파일이 생성되었습니다. OpenAI API 키를 설정해주세요."
fi

echo "✅ 설정 완료!"
echo ""
echo "🚀 서버 시작 방법:"
echo "   source venv_websurfer/bin/activate"
echo "   python magentic_websurfer_server.py"
echo ""
echo "📋 사전 준비사항:"
echo "   1. Docker가 실행 중이어야 합니다"
echo "   2. browser-interface의 Docker 컨테이너가 실행 중이어야 합니다"
echo "   3. .env 파일에서 OPENAI_API_KEY를 설정해야 합니다"
echo ""
echo "🔧 Docker 컨테이너 시작:"
echo "   npm start  # main browser-interface 서버"
echo "   # 웹 인터페이스에서 Docker 컨테이너 빌드 및 시작"
