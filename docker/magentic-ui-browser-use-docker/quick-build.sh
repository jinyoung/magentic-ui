#!/bin/bash

# 빠른 빌드 및 테스트 스크립트
echo "🐳 Magentic UI Browser-Use Docker 이미지 빌드 시작..."

# 이미지 이름 설정
IMAGE_NAME="magentic-ui-browser-use"
CONTAINER_NAME="magentic-ui-browser-use-test"

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Docker 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
if docker build -t $IMAGE_NAME .; then
    echo "✅ 이미지 빌드 성공!"
else
    echo "❌ 이미지 빌드 실패!"
    exit 1
fi

# 컨테이너 실행
echo "🚀 컨테이너 실행 중..."
docker run -d \
    --name $CONTAINER_NAME \
    -p 6080:6080 \
    -p 37367:37367 \
    -p 5001:5001 \
    $IMAGE_NAME

# 서비스가 시작될 때까지 대기
echo "⏳ 서비스 시작 대기 중..."
sleep 10

# 헬스 체크
echo "🔍 서비스 상태 확인 중..."
echo ""

echo "📋 Browser-Use API 헬스체크:"
if curl -s http://localhost:5001/health | grep -q "healthy"; then
    echo "✅ Browser-Use API 서버 정상 동작"
else
    echo "❌ Browser-Use API 서버 응답 없음"
fi

echo ""
echo "📋 Playwright 서버 확인:"
if curl -s http://localhost:37367 >/dev/null 2>&1; then
    echo "✅ Playwright 서버 접근 가능"
else
    echo "❌ Playwright 서버 접근 불가"
fi

echo ""
echo "🌐 접속 정보:"
echo "   VNC 웹뷰어:   http://localhost:6080"
echo "   Playwright:   ws://localhost:37367/default"
echo "   Browser-Use:  http://localhost:5001"
echo ""
echo "📋 테스트 명령어:"
echo "   헬스체크:     curl http://localhost:5001/health"
echo "   상태조회:     curl http://localhost:5001/status"
echo "   태스크실행:   curl -X POST -H 'Content-Type: application/json' -d '{\"task\":\"Google 홈페이지로 이동하기\"}' http://localhost:5001/execute"
echo ""
echo "🔍 로그 확인:    docker logs -f $CONTAINER_NAME"
echo "🛑 컨테이너 중지: docker stop $CONTAINER_NAME"
