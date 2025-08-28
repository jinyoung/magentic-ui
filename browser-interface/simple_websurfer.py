#!/usr/bin/env python3
"""
간단한 Magentic UI WebSurfer 서버 (5002 포트)
"""

import asyncio
import json
import logging
import base64
import os
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS

# Playwright 임포트
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# nest_asyncio 설정
import nest_asyncio
nest_asyncio.apply()

# Flask 앱 설정
app = Flask(__name__)
CORS(app)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 글로벌 변수
playwright_instance = None
browser = None
current_page = None

async def connect_browser():
    """브라우저에 연결"""
    global playwright_instance, browser
    
    try:
        if not playwright_instance:
            playwright_instance = await async_playwright().start()
        
        if not browser:
            # Docker 컨테이너의 Playwright WebSocket에 연결
            browser = await playwright_instance.chromium.connect("ws://localhost:37367/default")
            logger.info("✅ Playwright 브라우저 연결 성공")
            
        return browser
    except Exception as e:
        logger.error(f"❌ 브라우저 연결 실패: {e}")
        return None

async def get_page():
    """현재 페이지 가져오기 또는 새 페이지 생성"""
    global current_page
    
    browser = await connect_browser()
    if not browser:
        return None
        
    try:
        if not current_page:
            current_page = await browser.new_page()
            logger.info("✅ 새 페이지 생성됨")
        return current_page
    except Exception as e:
        logger.error(f"❌ 페이지 생성 실패: {e}")
        return None

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "message": "Simple Magentic UI WebSurfer Server",
        "port": 5002,
        "timestamp": datetime.now().isoformat(),
        "playwright_available": PLAYWRIGHT_AVAILABLE
    })

@app.route('/connect', methods=['POST'])
def connect_endpoint():
    """브라우저 연결"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        browser = loop.run_until_complete(connect_browser())
        
        if browser:
            return jsonify({
                "success": True,
                "message": "브라우저 연결 성공"
            })
        else:
            return jsonify({
                "success": False,
                "message": "브라우저 연결 실패"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"연결 오류: {str(e)}"
        }), 500

@app.route('/navigate', methods=['POST'])
def navigate():
    """페이지 이동"""
    try:
        data = request.get_json()
        url = data.get('url', 'https://example.com')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def nav():
            page = await get_page()
            if not page:
                return None
            await page.goto(url)
            title = await page.title()
            return {"url": url, "title": title}
        
        result = loop.run_until_complete(nav())
        
        if result:
            return jsonify({
                "success": True,
                "message": f"페이지 이동 성공: {url}",
                "data": result
            })
        else:
            return jsonify({
                "success": False,
                "message": "페이지 이동 실패"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"이동 오류: {str(e)}"
        }), 500

@app.route('/screenshot', methods=['GET'])
def take_screenshot():
    """스크린샷 촬영"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def screenshot():
            page = await get_page()
            if not page:
                return None
            screenshot_bytes = await page.screenshot()
            return base64.b64encode(screenshot_bytes).decode()
        
        result = loop.run_until_complete(screenshot())
        
        if result:
            return jsonify({
                "success": True,
                "message": "스크린샷 촬영 성공",
                "screenshot": result
            })
        else:
            return jsonify({
                "success": False,
                "message": "스크린샷 촬영 실패"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"스크린샷 오류: {str(e)}"
        }), 500

@app.route('/click', methods=['POST'])
def click_element():
    """요소 클릭"""
    try:
        data = request.get_json()
        selector = data.get('selector', 'body')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def click():
            page = await get_page()
            if not page:
                return False
            await page.click(selector)
            return True
        
        result = loop.run_until_complete(click())
        
        if result:
            return jsonify({
                "success": True,
                "message": f"클릭 성공: {selector}"
            })
        else:
            return jsonify({
                "success": False,
                "message": "클릭 실패"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"클릭 오류: {str(e)}"
        }), 500

@app.route('/type', methods=['POST'])
def type_text():
    """텍스트 입력"""
    try:
        data = request.get_json()
        selector = data.get('selector', 'input')
        text = data.get('text', '')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def type_():
            page = await get_page()
            if not page:
                return False
            await page.fill(selector, text)
            return True
        
        result = loop.run_until_complete(type_())
        
        if result:
            return jsonify({
                "success": True,
                "message": f"텍스트 입력 성공: {text}"
            })
        else:
            return jsonify({
                "success": False,
                "message": "텍스트 입력 실패"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"입력 오류: {str(e)}"
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """현재 상태 조회"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def status():
            page = await get_page()
            if not page:
                return None
            url = page.url
            title = await page.title()
            return {"url": url, "title": title}
        
        result = loop.run_until_complete(status())
        
        if result:
            return jsonify({
                "success": True,
                "message": "상태 조회 성공",
                "data": result
            })
        else:
            return jsonify({
                "success": False,
                "message": "상태 조회 실패"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"상태 조회 오류: {str(e)}"
        }), 500

if __name__ == '__main__':
    print("🚀 Simple Magentic UI WebSurfer Server 시작...")
    print("📡 포트: 5002")
    print("🌐 Health Check: http://localhost:5002/health")
    print("⚡ Playwright 지원:", PLAYWRIGHT_AVAILABLE)
    
    app.run(host='0.0.0.0', port=5002, debug=False)
