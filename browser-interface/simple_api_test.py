#!/usr/bin/env python3
"""
매우 간단한 API 테스트
"""
import json
import time
import requests

def test_docker_connection():
    """Docker 브라우저 연결 테스트"""
    try:
        # noVNC 포트 테스트
        response = requests.get('http://localhost:6080', timeout=5)
        print(f"✅ noVNC 연결 성공: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ noVNC 연결 실패: {e}")
        return False

def test_playwright_connection():
    """Playwright WebSocket 연결 테스트"""
    try:
        from playwright.async_api import async_playwright
        import asyncio
        
        async def test_connection():
            playwright = await async_playwright().start()
            try:
                browser = await playwright.chromium.connect("ws://localhost:37367/default")
                print("✅ Playwright WebSocket 연결 성공")
                
                # 간단한 브라우저 작업 테스트
                page = await browser.new_page()
                await page.goto("https://www.google.com")
                title = await page.title()
                print(f"✅ 페이지 제목: {title}")
                
                await browser.close()
                await playwright.stop()
                return True
            except Exception as e:
                print(f"❌ Playwright 연결 실패: {e}")
                await playwright.stop()
                return False
        
        return asyncio.run(test_connection())
    except Exception as e:
        print(f"❌ Playwright 테스트 실패: {e}")
        return False

def simulate_websurfer_task():
    """WebSurfer 태스크 시뮬레이션"""
    try:
        from playwright.async_api import async_playwright
        import asyncio
        
        async def run_task():
            playwright = await async_playwright().start()
            try:
                browser = await playwright.chromium.connect("ws://localhost:37367/default")
                page = await browser.new_page()
                
                print("🚀 태스크 시작: Google에서 'Playwright' 검색하기")
                
                # Google 홈페이지 방문
                await page.goto("https://www.google.com")
                print("📍 Google 홈페이지 방문 완료")
                
                # 검색창 찾기 및 텍스트 입력
                search_box = page.locator('textarea[name="q"], input[name="q"]')
                await search_box.fill("Playwright")
                print("⌨️  검색어 'Playwright' 입력 완료")
                
                # 검색 실행
                await search_box.press("Enter")
                await page.wait_for_load_state("networkidle")
                print("🔍 검색 실행 완료")
                
                # 결과 확인
                title = await page.title()
                url = page.url
                print(f"✅ 결과 페이지: {title}")
                print(f"🌐 현재 URL: {url}")
                
                # 스크린샷 촬영
                screenshot = await page.screenshot()
                print(f"📸 스크린샷 촬영 완료: {len(screenshot)} bytes")
                
                await browser.close()
                await playwright.stop()
                
                return {
                    "success": True,
                    "title": title,
                    "url": url,
                    "screenshot_size": len(screenshot)
                }
                
            except Exception as e:
                print(f"❌ 태스크 실행 실패: {e}")
                await playwright.stop()
                return {"success": False, "error": str(e)}
        
        return asyncio.run(run_task())
    except Exception as e:
        print(f"❌ 태스크 시뮬레이션 실패: {e}")
        return {"success": False, "error": str(e)}

if __name__ == '__main__':
    print("🤖 Magentic UI WebSurfer API 테스트 시작\n")
    
    # 1. Docker 연결 테스트
    print("1️⃣ Docker 브라우저 연결 테스트")
    docker_ok = test_docker_connection()
    print()
    
    # 2. Playwright 연결 테스트
    print("2️⃣ Playwright WebSocket 연결 테스트")
    playwright_ok = test_playwright_connection()
    print()
    
    # 3. 간단한 브라우저 태스크 실행
    if docker_ok and playwright_ok:
        print("3️⃣ WebSurfer 태스크 시뮬레이션")
        result = simulate_websurfer_task()
        print()
        print("📊 최종 결과:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("❌ 연결 실패로 태스크 시뮬레이션 건너뜀")
    
    print("\n✅ 테스트 완료!")

