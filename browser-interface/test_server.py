#!/usr/bin/env python3
"""
간단한 테스트 서버 - WebSurfer 서버 디버깅용
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "message": "Simple test server is running",
        "timestamp": "2024-12-08"
    })

@app.route('/connect', methods=['POST'])
def connect_browser():
    """브라우저 연결 테스트"""
    data = request.get_json() or {}
    ws_url = data.get('ws_url', 'ws://localhost:37367/default')
    
    return jsonify({
        "success": True,
        "message": f"브라우저 연결 테스트 완료: {ws_url}"
    })

@app.route('/test/docker', methods=['GET'])
def test_docker():
    """Docker 컨테이너 연결 테스트"""
    try:
        # noVNC 포트 테스트
        response = requests.get('http://localhost:6080', timeout=5)
        novnc_status = "연결됨" if response.status_code == 200 else "연결 실패"
    except:
        novnc_status = "연결 실패"
    
    return jsonify({
        "success": True,
        "novnc_status": novnc_status,
        "playwright_ws": "ws://localhost:37367/default",
        "message": "Docker 컨테이너 테스트 완료"
    })

@app.route('/execute', methods=['POST'])
def execute_task():
    """간단한 태스크 실행 시뮬레이션"""
    data = request.get_json()
    if not data or 'task' not in data:
        return jsonify({
            "success": False,
            "error": "태스크가 제공되지 않았습니다."
        }), 400
    
    task = data['task']
    
    # 간단한 응답 시뮬레이션
    return jsonify({
        "success": True,
        "task": task,
        "message": f"태스크 '{task}' 실행 시뮬레이션 완료",
        "action_taken": {
            "tool_name": "visit_url",
            "tool_args": {"url": "https://google.com"},
            "explanation": "Google 홈페이지로 이동합니다"
        },
        "current_url": "https://google.com",
        "current_title": "Google"
    })

if __name__ == '__main__':
    print("🧪 간단한 테스트 서버 시작 중...")
    print("📋 테스트 엔드포인트:")
    print("  - GET  /health       - 헬스 체크")
    print("  - POST /connect      - 브라우저 연결 테스트")
    print("  - GET  /test/docker  - Docker 컨테이너 테스트")
    print("  - POST /execute      - 태스크 실행 시뮬레이션")
    print()
    
    app.run(host='0.0.0.0', port=5003, debug=True)
