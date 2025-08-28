#!/bin/bash

# Browser-Use Docker API 테스트 스크립트
echo "🧪 Browser-Use Docker API 테스트 시작..."

# 기본 설정
HOST="localhost"
PORT="5001"
BASE_URL="http://${HOST}:${PORT}"

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 테스트 함수
test_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local data=$3
    
    echo -n "🔍 Testing ${method} ${endpoint}... "
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "${BASE_URL}${endpoint}")
    else
        response=$(curl -s -w "%{http_code}" "${BASE_URL}${endpoint}")
    fi
    
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ OK${NC}"
        if echo "$body" | grep -q '"success":true'; then
            echo -e "   ${GREEN}Response: $(echo "$body" | jq -c . 2>/dev/null || echo "$body")${NC}"
        else
            echo -e "   ${YELLOW}Warning: Success field is false${NC}"
        fi
    else
        echo -e "${RED}❌ Failed (HTTP $http_code)${NC}"
        echo -e "   ${RED}Response: $body${NC}"
    fi
    echo ""
}

# 컨테이너가 실행 중인지 확인
echo "🔍 컨테이너 상태 확인..."
if ! docker ps | grep -q "magentic-ui-browser-use"; then
    echo -e "${RED}❌ Browser-Use 컨테이너가 실행 중이 아닙니다.${NC}"
    echo "다음 명령어로 컨테이너를 시작하세요:"
    echo "cd docker/magentic-ui-browser-use-docker && ./quick-build.sh"
    exit 1
fi

echo -e "${GREEN}✅ 컨테이너가 실행 중입니다.${NC}"
echo ""

# API 엔드포인트 테스트
echo "📋 API 엔드포인트 테스트 시작..."
echo ""

# 헬스 체크
test_endpoint "/health"

# 상태 조회
test_endpoint "/status"

# 테스트 엔드포인트
test_endpoint "/test"

# 태스크 예시 조회
test_endpoint "/tasks/examples"

# 간단한 태스크 실행 테스트
echo "🚀 간단한 태스크 실행 테스트..."
test_endpoint "/execute" "POST" '{"task":"Google 홈페이지로 이동하기"}'

echo "🎉 API 테스트 완료!"
echo ""
echo "📋 추가 테스트 명령어:"
echo "   복잡한 태스크: curl -X POST -H 'Content-Type: application/json' -d '{\"task\":\"Google에서 browser automation 검색하기\"}' ${BASE_URL}/execute"
echo "   VNC 접속:     http://localhost:6080"
echo "   로그 확인:    docker logs -f magentic-ui-browser-use-test"
