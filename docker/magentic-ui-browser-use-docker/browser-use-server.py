#!/usr/bin/env python3
"""
Browser-Use Server for Docker Container
컨테이너 내부에서 실행되는 browser-use API 서버
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any
import traceback

from flask import Flask, request, jsonify
from flask_cors import CORS
import nest_asyncio

# browser-use 관련 임포트
try:
    from browser_use import Agent
    BROWSER_USE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: browser-use not available: {e}")
    BROWSER_USE_AVAILABLE = False

# Flask 앱 설정
app = Flask(__name__)
CORS(app)
nest_asyncio.apply()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContainerBrowserController:
    def __init__(self):
        self.agent = None
        self.last_result = None

    async def execute_task(self, task: str) -> Dict[str, Any]:
        """자연어 태스크 실행"""
        if not BROWSER_USE_AVAILABLE:
            return {
                "success": False,
                "error": "browser-use가 설치되지 않았습니다."
            }
        
        try:
            # 환경변수 설정
            os.environ['DISPLAY'] = ':99'
            
            # browser-use Agent 생성 (매번 새로 생성)
            logger.info(f"태스크 실행 시작: {task}")
            
            self.agent = Agent(
                task=task,
                llm_model="gpt-4o-mini"  # 또는 사용 가능한 다른 모델
            )
            
            # 태스크 실행
            result = await self.agent.run()
            
            self.last_result = {
                "success": True,
                "result": str(result),
                "task": task,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"태스크 실행 완료: {task}")
            return self.last_result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "task": task,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.error(f"태스크 실행 실패: {e}")
            self.last_result = error_result
            return error_result

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        return {
            "success": True,
            "browser_use_available": BROWSER_USE_AVAILABLE,
            "agent_active": self.agent is not None,
            "last_result": self.last_result,
            "timestamp": datetime.now().isoformat(),
            "display": os.environ.get('DISPLAY', 'not_set')
        }

# 전역 컨트롤러 인스턴스
controller = ContainerBrowserController()

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "browser_use_available": BROWSER_USE_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
        "environment": "docker_container"
    })

@app.route('/status', methods=['GET'])
def get_status():
    """상태 조회"""
    return jsonify(controller.get_status())

@app.route('/execute', methods=['POST'])
def execute_task():
    """자연어 태스크 실행"""
    data = request.get_json()
    if not data or 'task' not in data:
        return jsonify({
            "success": False,
            "error": "태스크가 제공되지 않았습니다."
        }), 400
    
    task = data['task']
    
    # 새로운 이벤트 루프 생성
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(controller.execute_task(task))
        return jsonify(result)
    finally:
        loop.close()

@app.route('/tasks/examples', methods=['GET'])
def get_task_examples():
    """태스크 예시 목록"""
    examples = [
        {
            "title": "웹사이트 검색",
            "task": "Google에서 'browser automation' 검색하기",
            "description": "구글에서 자동화 관련 검색을 수행합니다"
        },
        {
            "title": "웹사이트 방문",
            "task": "GitHub 홈페이지로 이동하기",
            "description": "GitHub 메인 페이지로 이동합니다"
        },
        {
            "title": "정보 수집",
            "task": "현재 페이지의 제목과 주요 내용 요약하기",
            "description": "페이지의 핵심 정보를 추출합니다"
        },
        {
            "title": "폼 작성",
            "task": "검색창에 'Playwright' 입력하고 검색하기",
            "description": "웹 폼에 텍스트를 입력하고 제출합니다"
        }
    ]
    
    return jsonify({
        "success": True,
        "examples": examples
    })

@app.route('/test', methods=['GET'])
def test_endpoint():
    """테스트 엔드포인트"""
    return jsonify({
        "success": True,
        "message": "Browser-Use Docker 서버가 정상적으로 실행 중입니다!",
        "timestamp": datetime.now().isoformat(),
        "environment_info": {
            "display": os.environ.get('DISPLAY'),
            "python_path": os.environ.get('PATH'),
            "browser_use_available": BROWSER_USE_AVAILABLE
        }
    })

if __name__ == '__main__':
    print("🐳 Browser-Use Docker Server 시작 중...")
    print("📋 사용 가능한 엔드포인트:")
    print("  - GET  /health       - 헬스 체크")
    print("  - GET  /status       - 상태 조회")
    print("  - POST /execute      - 자연어 태스크 실행")
    print("  - GET  /tasks/examples - 태스크 예시 목록")
    print("  - GET  /test         - 테스트 엔드포인트")
    print()
    
    if not BROWSER_USE_AVAILABLE:
        print("⚠️  browser-use가 설치되지 않았습니다.")
        print()
    
    # 컨테이너 내부에서 실행하므로 0.0.0.0으로 바인딩
    app.run(host='0.0.0.0', port=5001, debug=False)
