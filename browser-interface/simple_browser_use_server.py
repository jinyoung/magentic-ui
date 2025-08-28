#!/usr/bin/env python3
"""
Simplified Browser-Use Server for Magentic UI Browser Interface
browser-use 라이브러리 없이 순수 Playwright로 동일한 기능 구현
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

# Playwright 관련 임포트
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Playwright not available: {e}")
    print("Install with: pip install playwright")
    PLAYWRIGHT_AVAILABLE = False

# OpenAI 임포트 (간단한 자연어 처리용)
try:
    import openai
    import os
    OPENAI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: OpenAI not available: {e}")
    print("Install with: pip install openai")
    OPENAI_AVAILABLE = False

# Flask 앱 설정
app = Flask(__name__)
CORS(app)
nest_asyncio.apply()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleBrowserController:
    def __init__(self):
        self.browser = None
        self.page = None
        self.connected = False
        self.openai_client = None
        
        # OpenAI 클라이언트 초기화
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)

    async def connect_to_browser(self, ws_url: str = "ws://localhost:37367/default"):
        """Playwright 브라우저에 연결"""
        if not PLAYWRIGHT_AVAILABLE:
            return False
            
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
            
            self.connected = True
            logger.info("브라우저에 성공적으로 연결되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"브라우저 연결 실패: {e}")
            self.connected = False
            return False

    async def execute_simple_task(self, task: str) -> Dict[str, Any]:
        """간단한 자연어 태스크 실행 (OpenAI 없이)"""
        if not self.connected or not self.page:
            success = await self.connect_to_browser()
            if not success:
                return {
                    "success": False,
                    "error": "브라우저에 연결할 수 없습니다."
                }
        
        try:
            # 간단한 태스크 처리 로직
            task_lower = task.lower()
            
            if "google" in task_lower and "검색" in task_lower:
                # Google 검색 태스크
                search_query = self._extract_search_query(task)
                await self.page.goto("https://www.google.com")
                await self.page.wait_for_selector('input[name="q"]')
                await self.page.fill('input[name="q"]', search_query)
                await self.page.press('input[name="q"]', 'Enter')
                await self.page.wait_for_load_state('networkidle')
                
                result_message = f"Google에서 '{search_query}' 검색을 완료했습니다."
                
            elif "이동" in task_lower or "방문" in task_lower:
                # URL 방문 태스크
                url = self._extract_url(task)
                if url:
                    await self.page.goto(url)
                    await self.page.wait_for_load_state('networkidle')
                    result_message = f"{url} 페이지로 이동했습니다."
                else:
                    result_message = "URL을 찾을 수 없어서 작업을 수행할 수 없습니다."
                    
            elif "스크린샷" in task_lower:
                # 스크린샷 촬영
                screenshot_path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await self.page.screenshot(path=screenshot_path)
                result_message = f"스크린샷을 {screenshot_path}에 저장했습니다."
                
            else:
                # 기본 응답
                result_message = f"'{task}' 태스크를 이해했지만, 구체적인 구현이 필요합니다."
            
            # 현재 페이지 정보 수집
            current_url = self.page.url
            current_title = await self.page.title()
            
            return {
                "success": True,
                "result": result_message,
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

    def _extract_search_query(self, task: str) -> str:
        """태스크에서 검색어 추출"""
        # 간단한 검색어 추출 로직
        if "'" in task:
            parts = task.split("'")
            if len(parts) >= 2:
                return parts[1]
        elif '"' in task:
            parts = task.split('"')
            if len(parts) >= 2:
                return parts[1]
        
        # 기본 검색어
        return "Playwright"

    def _extract_url(self, task: str) -> str:
        """태스크에서 URL 추출"""
        import re
        # URL 패턴 찾기
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, task)
        if urls:
            return urls[0]
        
        # 일반적인 도메인 이름 찾기
        if "google.com" in task.lower():
            return "https://www.google.com"
        elif "naver.com" in task.lower():
            return "https://www.naver.com"
        
        return None

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
                "current_url": self.page.url,
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
                "url": self.page.url,
                "title": await self.page.title(),
                "connected": self.connected
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# 전역 컨트롤러 인스턴스
controller = SimpleBrowserController()

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "playwright_available": PLAYWRIGHT_AVAILABLE,
        "openai_available": OPENAI_AVAILABLE,
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
        result = loop.run_until_complete(controller.execute_simple_task(task))
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
            "title": "페이지 방문",
            "task": "https://www.naver.com 이동하기",
            "description": "지정된 URL로 페이지를 이동합니다"
        },
        {
            "title": "스크린샷",
            "task": "현재 페이지 스크린샷 촬영하기",
            "description": "현재 보고 있는 페이지의 스크린샷을 저장합니다"
        }
    ]
    
    return jsonify({
        "success": True,
        "examples": examples
    })

if __name__ == '__main__':
    print("🤖 Simple Browser-Use Server 시작 중...")
    print("📋 사용 가능한 엔드포인트:")
    print("  - GET  /health       - 헬스 체크")
    print("  - POST /connect      - 브라우저 연결")
    print("  - POST /execute      - 자연어 태스크 실행")
    print("  - POST /screenshot   - 스크린샷 촬영")
    print("  - GET  /page_info    - 페이지 정보 조회")
    print("  - GET  /tasks/examples - 태스크 예시 목록")
    print()
    
    if not PLAYWRIGHT_AVAILABLE:
        print("⚠️  Playwright가 설치되지 않았습니다.")
        print("   설치 명령: pip install playwright")
        print()
    
    # macOS AirPlay 충돌 방지를 위해 포트 5003 사용
    app.run(host='0.0.0.0', port=5003, debug=True)
