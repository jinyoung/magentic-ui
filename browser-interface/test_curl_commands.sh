#!/bin/bash

echo "🚀 Magentic UI WebSurfer cURL API 테스트"
echo "========================================"

# 간단한 REST API 서버 시작
echo "1️⃣ 간단한 API 서버 시작 (포트 5004)"
source venv_websurfer/bin/activate

cat > mini_server.py << 'EOF'
from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
from playwright.async_api import async_playwright

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "message": "Mini WebSurfer API"})

@app.route('/simple_browse', methods=['POST'])
def simple_browse():
    data = request.get_json()
    url = data.get('url', 'https://example.com')
    
    async def browse():
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect("ws://localhost:37367/default")
        page = await browser.new_page()
        await page.goto(url)
        title = await page.title()
        await browser.close()
        await playwright.stop()
        return {"title": title, "url": url}
    
    result = asyncio.run(browse())
    return jsonify({"success": True, "result": result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=False)
EOF

python mini_server.py &
SERVER_PID=$!
sleep 3

echo ""
echo "2️⃣ Health Check 테스트"
curl -s -X GET http://localhost:5004/health | python3 -m json.tool

echo ""
echo "3️⃣ 간단한 브라우징 테스트"
curl -s -X POST http://localhost:5004/simple_browse \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' | python3 -m json.tool

echo ""
echo "4️⃣ Google 방문 테스트"
curl -s -X POST http://localhost:5004/simple_browse \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.google.com"}' | python3 -m json.tool

echo ""
echo "5️⃣ 서버 종료"
kill $SERVER_PID 2>/dev/null

echo ""
echo "✅ cURL API 테스트 완료!"

