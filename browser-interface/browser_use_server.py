#!/usr/bin/env python3
"""
Browser-Use Server for Magentic UI Browser Interface
AI를 통한 자연어 브라우저 제어 서버
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import traceback

from flask import Flask, request, jsonify
from flask_cors import CORS
import nest_asyncio

# browser-use 관련 임포트
try:
    from browser_use import Agent
    from playwright.async_api import async_playwright, Browser, Page
    BROWSER_USE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: browser-use not available: {e}")
    print("Install with: pip install browser-use")
    BROWSER_USE_AVAILABLE = False

# Flask 앱 설정
app = Flask(__name__)
CORS(app)
nest_asyncio.apply()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 변수
browser: Optional[Browser] = None
page: Optional[Page] = None
agent: Optional[Agent] = None

class BrowserController:
    def __init__(self):
        self.browser = None
        self.page = None
        self.agent = None
        self.connected = False

    async def connect_to_browser(self, ws_url: str = "ws://localhost:37367/default"):
        """Playwright 브라우저에 연결"""
        try:
            playwright = await async_playwright().start()
            
            # 기존 연결 해제
            if self.browser:
                await self.browser.close()
            
            # 원격 브라우저에 연결 (WebSocket 방식)
            self.browser = await playwright.chromium.connect(ws_url)
            
            # 기존 페이지 가져오기 또는 새 페이지 생성
            contexts = self.browser.contexts
            if contexts and len(contexts) > 0:
                pages = contexts[0].pages
                if pages and len(pages) > 0:
                    self.page = pages[0]
                else:
                    self.page = await contexts[0].new_page()
            else:
                context = await self.browser.new_context()
                self.page = await context.new_page()
            
            # browser-use Agent 초기화
            if BROWSER_USE_AVAILABLE:
                self.agent = Agent(
                    task="",
                    llm_model="gpt-4o-mini",  # 또는 사용 가능한 다른 모델
                    browser=self.browser
                )
            
            self.connected = True
            logger.info("브라우저에 성공적으로 연결되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"브라우저 연결 실패: {e}")
            self.connected = False
            return False

    async def execute_task(self, task: str) -> Dict[str, Any]:
        """자연어 태스크 실행"""
        if not BROWSER_USE_AVAILABLE:
            return {
                "success": False,
                "error": "browser-use가 설치되지 않았습니다. pip install browser-use로 설치하세요."
            }
        
        if not self.connected or not self.agent:
            success = await self.connect_to_browser()
            if not success:
                return {
                    "success": False,
                    "error": "브라우저에 연결할 수 없습니다."
                }
        
        try:
            # Agent에 새 태스크 설정
            self.agent.task = task
            
            # 태스크 실행
            result = await self.agent.run()
            
            # 현재 페이지 정보 수집
            current_url = await self.page.url if self.page else "unknown"
            current_title = await self.page.title() if self.page else "unknown"
            
            return {
                "success": True,
                "result": str(result),
                "current_url": current_url,
                "current_title": current_title,
                "task": task
            }
            
        except Exception as e:
            logger.error(f"태스크 실행 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    async def take_screenshot(self) -> Dict[str, Any]:
        """스크린샷 촬영"""
        if not self.page:
            return {
                "success": False,
                "error": "활성화된 페이지가 없습니다."
            }
        
        try:
            screenshot_path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await self.page.screenshot(path=screenshot_path)
            
            return {
                "success": True,
                "screenshot_path": screenshot_path,
                "current_url": await self.page.url,
                "current_title": await self.page.title()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_page_info(self) -> Dict[str, Any]:
        """현재 페이지 정보 조회"""
        if not self.page:
            return {
                "success": False,
                "error": "활성화된 페이지가 없습니다."
            }
        
        try:
            return {
                "success": True,
                "url": await self.page.url,
                "title": await self.page.title(),
                "connected": self.connected
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# 전역 컨트롤러 인스턴스
controller = BrowserController()

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "browser_use_available": BROWSER_USE_AVAILABLE,
        "connected": controller.connected,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/connect', methods=['POST'])
def connect_browser():
    """브라우저 연결"""
    data = request.get_json() or {}
    ws_url = data.get('ws_url', 'ws://localhost:37367/default')
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(controller.connect_to_browser(ws_url))
        return jsonify({
            "success": success,
            "message": "브라우저 연결 성공" if success else "브라우저 연결 실패"
        })
    finally:
        loop.close()

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
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(controller.execute_task(task))
        return jsonify(result)
    finally:
        loop.close()

@app.route('/screenshot', methods=['POST'])
def take_screenshot():
    """스크린샷 촬영"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(controller.take_screenshot())
        return jsonify(result)
    finally:
        loop.close()

@app.route('/page_info', methods=['GET'])
def get_page_info():
    """페이지 정보 조회"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(controller.get_page_info())
        return jsonify(result)
    finally:
        loop.close()

@app.route('/tasks/examples', methods=['GET'])
def get_task_examples():
    """태스크 예시 목록"""
    examples = [
        {
            "title": "웹사이트 이동",
            "task": "Google에서 'Playwright' 검색하기",
            "description": "구글 홈페이지에서 검색어를 입력하고 검색합니다"
        },
        {
            "title": "폼 작성",
            "task": "이메일 입력 필드에 'test@example.com' 입력하기",
            "description": "페이지의 이메일 입력 필드를 찾아서 값을 입력합니다"
        },
        {
            "title": "링크 클릭",
            "task": "첫 번째 검색 결과 클릭하기",
            "description": "검색 결과 목록에서 첫 번째 링크를 클릭합니다"
        },
        {
            "title": "스크롤",
            "task": "페이지 맨 아래로 스크롤하기",
            "description": "페이지를 스크롤하여 더 많은 콘텐츠를 확인합니다"
        },
        {
            "title": "텍스트 추출",
            "task": "페이지 제목과 첫 번째 문단 내용 가져오기",
            "description": "페이지의 주요 텍스트 정보를 추출합니다"
        }
    ]
    
    return jsonify({
        "success": True,
        "examples": examples
    })

if __name__ == '__main__':
    print("🤖 Browser-Use Server 시작 중...")
    print("📋 사용 가능한 엔드포인트:")
    print("  - GET  /health       - 헬스 체크")
    print("  - POST /connect      - 브라우저 연결")
    print("  - POST /execute      - 자연어 태스크 실행")
    print("  - POST /screenshot   - 스크린샷 촬영")
    print("  - GET  /page_info    - 페이지 정보 조회")
    print("  - GET  /tasks/examples - 태스크 예시 목록")
    print()
    
    if not BROWSER_USE_AVAILABLE:
        print("⚠️  browser-use가 설치되지 않았습니다.")
        print("   설치 명령: pip install browser-use")
        print()
    
    # macOS AirPlay 충돌 방지를 위해 포트 5001 사용
    app.run(host='0.0.0.0', port=5001, debug=True)
