#!/usr/bin/env python3
"""
Magentic UI WebSurfer Server - A simplified version of WebSurfer for browser automation
AI를 통한 자연어 브라우저 제어 서버 (Magentic UI 기반)
"""

import asyncio
import json
import logging
import base64
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
import traceback

from flask import Flask, request, jsonify
from flask_cors import CORS
import nest_asyncio

# Playwright 및 관련 임포트
try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Playwright not available: {e}")
    print("Install with: pip install playwright")
    PLAYWRIGHT_AVAILABLE = False

# OpenAI 임포트
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: OpenAI not available: {e}")
    print("Install with: pip install openai")
    OPENAI_AVAILABLE = False

# PIL for image processing
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PIL not available: {e}")
    print("Install with: pip install Pillow")
    PIL_AVAILABLE = False

# Flask 앱 설정
app = Flask(__name__)
CORS(app)
nest_asyncio.apply()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSurfer 프롬프트
WEB_SURFER_SYSTEM_MESSAGE = """
You are a helpful assistant that controls a web browser. You are to utilize this web browser to answer requests.
The date today is: {date_today}

You will be given a screenshot of the current page and a list of targets that represent the interactive elements on the page.
The list of targets is a JSON array of objects, each representing an interactive element on the page.
Each object has the following properties:
- id: the numeric ID of the element
- name: the name of the element
- role: the role of the element
- tools: the tools that can be used to interact with the element

You have access to the following tools:
- stop_action: Perform no action and provide an answer with a summary of past actions and observations
- answer_question: Used to answer questions about the current webpage's content
- click: Click on a target element using its ID
- hover: Hover the mouse over a target element using its ID
- input_text: Type text into an input field, with options to delete existing text and press enter
- select_option: Select an option from a dropdown/select menu
- scroll_up: Scroll the viewport up towards the beginning
- scroll_down: Scroll the viewport down towards the end
- visit_url: Navigate directly to a provided URL
- web_search: Perform a web search query on Bing.com
- history_back: Go back one page in browser history
- refresh_page: Refresh the current page
- keypress: Press one or more keyboard keys in sequence
- sleep: Wait briefly for page loading or to improve task success

When deciding between tools, follow these guidelines:
1) if the request is completed, or you are unsure what to do, use the stop_action tool to respond to the request and include complete information
2) If the request does not require any action but answering a question, use the answer_question tool before using any other tool or stop_action tool
3) IMPORTANT: if an option exists and its selector is focused, always use the select_option tool to select it before any other action.
4) If the request requires an action make sure to use an element index that is in the list provided
5) If the action can be addressed by the content of the viewport visible in the image consider actions like clicking, inputing text or hovering
6) If the action cannot be addressed by the content of the viewport, consider scrolling, visiting a new page or web search
7) If you need to answer a question or request with text that is outside the viewport use the answer_question tool, otherwise always use the stop_action tool to answer questions with the viewport content.

Helpful tips to ensure success:
- Handle popups/cookies by accepting or closing them
- Use scroll to find elements you are looking for. However, for answering questions, you should use the answer_question tool.
- If stuck, try alternative approaches.
- VERY IMPORTANT: DO NOT REPEAT THE SAME ACTION IF IT HAS AN ERROR OR OTHER FAILURE.
- When filling a form, make sure to scroll down to ensure you fill the entire form.

Output an answer in pure JSON format according to the following schema. The JSON object must be parsable as-is. DO NOT OUTPUT ANYTHING OTHER THAN JSON:

The JSON object should have the three components:
1. "tool_name": the name of the tool to use
2. "tool_args": a dictionary of arguments to pass to the tool
3. "explanation": Explain to the user the action to be performed and reason for doing so.

{{
"tool_name": "tool_name",
"tool_args": {{"arg_name": arg_value}},
"explanation": "explanation"
}}
"""

class SimplifiedPlaywrightController:
    """간소화된 Playwright 컨트롤러 - WebSurfer 핵심 기능만 포함"""
    
    def __init__(self, viewport_width: int = 1440, viewport_height: int = 1440):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self._page_script: str = self._load_page_script()
    
    def _load_page_script(self) -> str:
        """WebSurfer JavaScript 스크립트 로드"""
        script = """
        var WebSurfer = WebSurfer || (function () {
            let getInteractiveRects = function() {
                const results = {};
                let id = 0;
                
                // 모든 인터랙티브 요소를 찾기
                const selectors = [
                    'a[href]', 'button', 'input', 'select', 'textarea',
                    '[onclick]', '[role="button"]', '[role="link"]',
                    '[tabindex]', 'label[for]'
                ];
                
                selectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(element => {
                        if (element.offsetParent !== null) { // 보이는 요소만
                            const rect = element.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                element.setAttribute('__elementId', id.toString());
                                results[id.toString()] = {
                                    'rects': [{
                                        'left': rect.left,
                                        'top': rect.top,
                                        'right': rect.right,
                                        'bottom': rect.bottom,
                                        'width': rect.width,
                                        'height': rect.height
                                    }],
                                    'tag_name': element.tagName.toLowerCase(),
                                    'text': element.textContent ? element.textContent.trim().substring(0, 100) : '',
                                    'role': element.getAttribute('role') || element.tagName.toLowerCase(),
                                    'name': element.getAttribute('name') || element.getAttribute('id') || '',
                                    'value': element.value || ''
                                };
                                id++;
                            }
                        }
                    });
                });
                
                return results;
            };
            
            let getVisibleText = function() {
                const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
                const viewportWidth = window.innerWidth || document.documentElement.clientWidth;
                
                let textInView = "";
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                while (walker.nextNode()) {
                    const textNode = walker.currentNode;
                    const range = document.createRange();
                    range.selectNodeContents(textNode);
                    const rects = range.getClientRects();
                    
                    for (const rect of rects) {
                        const isVisible = rect.width > 0 && rect.height > 0 &&
                            rect.bottom >= 0 && rect.right >= 0 &&
                            rect.top <= viewportHeight && rect.left <= viewportWidth;
                        
                        if (isVisible) {
                            textInView += textNode.nodeValue.replace(/\\s+/g, " ");
                            if (textNode.parentNode) {
                                const parent = textNode.parentNode;
                                const style = window.getComputedStyle(parent);
                                if (["inline", "hidden", "none"].indexOf(style.display) === -1) {
                                    textInView += "\\n";
                                }
                            }
                            break;
                        }
                    }
                }
                
                return textInView.replace(/^\\s*\\n/gm, "").trim().replace(/\\n+/g, "\\n");
            };
            
            let getVisualViewport = function() {
                return {
                    'width': window.innerWidth,
                    'height': window.innerHeight,
                    'scrollWidth': document.documentElement.scrollWidth,
                    'scrollHeight': document.documentElement.scrollHeight,
                    'pageTop': window.pageYOffset || document.documentElement.scrollTop,
                    'pageLeft': window.pageXOffset || document.documentElement.scrollLeft
                };
            };
            
            return {
                getInteractiveRects: getInteractiveRects,
                getVisibleText: getVisibleText,
                getVisualViewport: getVisualViewport
            };
        })();
        """
        return script
    
    async def get_interactive_rects(self, page: Page) -> Dict[str, Any]:
        """페이지의 인터랙티브 요소들을 가져옴"""
        try:
            await page.evaluate(self._page_script)
            result = await page.evaluate("WebSurfer.getInteractiveRects();")
            return result if isinstance(result, dict) else {}
        except Exception as e:
            logger.error(f"Error getting interactive rects: {e}")
            return {}
    
    async def get_visible_text(self, page: Page) -> str:
        """페이지의 보이는 텍스트를 가져옴"""
        try:
            await page.evaluate(self._page_script)
            result = await page.evaluate("WebSurfer.getVisibleText();")
            return result if isinstance(result, str) else ""
        except Exception as e:
            logger.error(f"Error getting visible text: {e}")
            return ""
    
    async def get_visual_viewport(self, page: Page) -> Dict[str, Any]:
        """뷰포트 정보를 가져옴"""
        try:
            await page.evaluate(self._page_script)
            result = await page.evaluate("WebSurfer.getVisualViewport();")
            return result if isinstance(result, dict) else {}
        except Exception as e:
            logger.error(f"Error getting visual viewport: {e}")
            return {}
    
    async def get_screenshot(self, page: Page) -> bytes:
        """스크린샷 촬영"""
        try:
            screenshot = await page.screenshot(timeout=7000)
            return screenshot
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return b""
    
    async def click_element(self, page: Page, element_id: str) -> bool:
        """요소 클릭"""
        try:
            selector = f"[__elementId='{element_id}']"
            await page.wait_for_selector(selector, state="visible", timeout=5000)
            await page.click(selector)
            await page.wait_for_timeout(500)  # 잠시 대기
            return True
        except Exception as e:
            logger.error(f"Error clicking element {element_id}: {e}")
            return False
    
    async def input_text(self, page: Page, element_id: str, text: str, press_enter: bool = False, delete_existing: bool = False) -> bool:
        """텍스트 입력"""
        try:
            selector = f"[__elementId='{element_id}']"
            await page.wait_for_selector(selector, state="visible", timeout=5000)
            
            if delete_existing:
                await page.fill(selector, "")
            
            await page.type(selector, text)
            
            if press_enter:
                await page.keyboard.press("Enter")
            
            await page.wait_for_timeout(500)
            return True
        except Exception as e:
            logger.error(f"Error inputting text to element {element_id}: {e}")
            return False
    
    async def scroll_page(self, page: Page, direction: str) -> bool:
        """페이지 스크롤"""
        try:
            if direction.lower() == "up":
                await page.evaluate("window.scrollBy(0, -400);")
            else:
                await page.evaluate("window.scrollBy(0, 400);")
            await page.wait_for_timeout(500)
            return True
        except Exception as e:
            logger.error(f"Error scrolling {direction}: {e}")
            return False
    
    async def visit_url(self, page: Page, url: str) -> bool:
        """URL 방문"""
        try:
            await page.goto(url, wait_until="load", timeout=30000)
            await page.wait_for_timeout(1000)
            return True
        except Exception as e:
            logger.error(f"Error visiting URL {url}: {e}")
            return False
    
    async def go_back(self, page: Page) -> bool:
        """뒤로 가기"""
        try:
            await page.go_back(wait_until="load", timeout=10000)
            await page.wait_for_timeout(500)
            return True
        except Exception as e:
            logger.error(f"Error going back: {e}")
            return False
    
    async def refresh_page(self, page: Page) -> bool:
        """페이지 새로고침"""
        try:
            await page.reload(wait_until="load", timeout=10000)
            await page.wait_for_timeout(500)
            return True
        except Exception as e:
            logger.error(f"Error refreshing page: {e}")
            return False

def add_element_markers(screenshot_bytes: bytes, interactive_rects: Dict[str, Any]) -> bytes:
    """스크린샷에 요소 마커 추가"""
    if not PIL_AVAILABLE:
        return screenshot_bytes
    
    try:
        from io import BytesIO
        image = Image.open(BytesIO(screenshot_bytes))
        draw = ImageDraw.Draw(image)
        
        # 기본 폰트 사용
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        for element_id, rect_info in interactive_rects.items():
            if 'rects' in rect_info and rect_info['rects']:
                rect = rect_info['rects'][0]
                left, top = int(rect['left']), int(rect['top'])
                right, bottom = int(rect['right']), int(rect['bottom'])
                
                # 빨간 테두리 그리기
                draw.rectangle([left, top, right, bottom], outline="red", width=2)
                
                # 요소 ID 라벨 추가
                label = str(element_id)
                if font:
                    draw.text((left, max(0, top-15)), label, fill="red", font=font)
                else:
                    draw.text((left, max(0, top-15)), label, fill="red")
        
        # 이미지를 bytes로 변환
        output = BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()
    
    except Exception as e:
        logger.error(f"Error adding element markers: {e}")
        return screenshot_bytes

class MagenticWebSurferController:
    """Magentic UI WebSurfer 컨트롤러"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright_controller = SimplifiedPlaywrightController()
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
            
            # 원격 브라우저에 연결
            self.browser = await playwright.chromium.connect(ws_url)
            
            # 기존 컨텍스트와 페이지 가져오기 또는 새로 생성
            contexts = self.browser.contexts
            if contexts and len(contexts) > 0:
                self.context = contexts[0]
                pages = self.context.pages
                if pages and len(pages) > 0:
                    self.page = pages[0]
                else:
                    self.page = await self.context.new_page()
            else:
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
            
            # 뷰포트 설정
            await self.page.set_viewport_size({
                "width": self.playwright_controller.viewport_width,
                "height": self.playwright_controller.viewport_height
            })
            
            self.connected = True
            logger.info("브라우저에 성공적으로 연결되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"브라우저 연결 실패: {e}")
            self.connected = False
            return False
    
    def get_llm_response(self, task: str, screenshot_b64: str, visible_text: str, interactive_elements: List[Dict]) -> Dict[str, Any]:
        """LLM을 사용하여 다음 액션 결정"""
        if not self.openai_client:
            return {
                "success": False,
                "error": "OpenAI API가 설정되지 않았습니다."
            }
        
        try:
            # 프롬프트 구성
            date_today = datetime.now().strftime("%Y-%m-%d")
            system_message = WEB_SURFER_SYSTEM_MESSAGE.format(date_today=date_today)
            
            user_message = f"""
            The last request received was: {task}
            
            The webpage has the following text:
            {visible_text[:2000]}  # 텍스트 길이 제한
            
            Attached is a screenshot of the current page. In this screenshot, interactive elements are outlined in red boxes with numeric ID labels. Additional information about each visible element is listed below:
            
            {json.dumps(interactive_elements, indent=2)}
            """
            
            messages = [
                {"role": "system", "content": system_message},
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": user_message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_b64}"
                            }
                        }
                    ]
                }
            ]
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # 또는 gpt-4-vision-preview
                messages=messages,
                max_tokens=1000,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # JSON 응답 파싱
            try:
                action_json = json.loads(content)
                return {
                    "success": True,
                    "action": action_json
                }
            except json.JSONDecodeError:
                # JSON이 아닌 경우 stop_action으로 처리
                return {
                    "success": True,
                    "action": {
                        "tool_name": "stop_action",
                        "tool_args": {"answer": content},
                        "explanation": "LLM이 JSON 형식으로 응답하지 않아 정지합니다."
                    }
                }
                
        except Exception as e:
            logger.error(f"LLM 응답 오류: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """액션 실행"""
        if not self.page:
            return {"success": False, "error": "페이지가 연결되지 않았습니다."}
        
        tool_name = action.get("tool_name")
        tool_args = action.get("tool_args", {})
        explanation = action.get("explanation", "")
        
        try:
            if tool_name == "click":
                target_id = str(tool_args.get("target_id", ""))
                success = await self.playwright_controller.click_element(self.page, target_id)
                return {
                    "success": success,
                    "message": f"요소 {target_id} 클릭 {'성공' if success else '실패'}",
                    "explanation": explanation
                }
            
            elif tool_name == "input_text":
                field_id = str(tool_args.get("input_field_id", ""))
                text_value = tool_args.get("text_value", "")
                press_enter = tool_args.get("press_enter", False)
                delete_existing = tool_args.get("delete_existing_text", False)
                
                success = await self.playwright_controller.input_text(
                    self.page, field_id, text_value, press_enter, delete_existing
                )
                return {
                    "success": success,
                    "message": f"텍스트 입력 {'성공' if success else '실패'}: {text_value}",
                    "explanation": explanation
                }
            
            elif tool_name == "scroll_up":
                success = await self.playwright_controller.scroll_page(self.page, "up")
                return {
                    "success": success,
                    "message": f"위로 스크롤 {'성공' if success else '실패'}",
                    "explanation": explanation
                }
            
            elif tool_name == "scroll_down":
                success = await self.playwright_controller.scroll_page(self.page, "down")
                return {
                    "success": success,
                    "message": f"아래로 스크롤 {'성공' if success else '실패'}",
                    "explanation": explanation
                }
            
            elif tool_name == "visit_url":
                url = tool_args.get("url", "")
                success = await self.playwright_controller.visit_url(self.page, url)
                return {
                    "success": success,
                    "message": f"URL 방문 {'성공' if success else '실패'}: {url}",
                    "explanation": explanation
                }
            
            elif tool_name == "history_back":
                success = await self.playwright_controller.go_back(self.page)
                return {
                    "success": success,
                    "message": f"뒤로 가기 {'성공' if success else '실패'}",
                    "explanation": explanation
                }
            
            elif tool_name == "refresh_page":
                success = await self.playwright_controller.refresh_page(self.page)
                return {
                    "success": success,
                    "message": f"페이지 새로고침 {'성공' if success else '실패'}",
                    "explanation": explanation
                }
            
            elif tool_name == "web_search":
                query = tool_args.get("query", "")
                search_url = f"https://www.bing.com/search?q={query}"
                success = await self.playwright_controller.visit_url(self.page, search_url)
                return {
                    "success": success,
                    "message": f"웹 검색 {'성공' if success else '실패'}: {query}",
                    "explanation": explanation
                }
            
            elif tool_name == "sleep":
                duration = tool_args.get("duration", 3)
                await asyncio.sleep(duration)
                return {
                    "success": True,
                    "message": f"{duration}초 대기 완료",
                    "explanation": explanation
                }
            
            elif tool_name == "stop_action":
                answer = tool_args.get("answer", "작업이 완료되었습니다.")
                return {
                    "success": True,
                    "message": "작업 중지",
                    "answer": answer,
                    "explanation": explanation
                }
            
            elif tool_name == "answer_question":
                # 현재 페이지의 텍스트를 가져와서 질문에 답변
                visible_text = await self.playwright_controller.get_visible_text(self.page)
                question = tool_args.get("question", "")
                
                return {
                    "success": True,
                    "message": "질문 답변 완료",
                    "answer": f"질문: {question}\n\n페이지 내용 기반 답변: {visible_text[:1000]}...",
                    "explanation": explanation
                }
            
            else:
                return {
                    "success": False,
                    "error": f"지원하지 않는 도구: {tool_name}",
                    "explanation": explanation
                }
                
        except Exception as e:
            logger.error(f"액션 실행 오류: {e}")
            return {
                "success": False,
                "error": str(e),
                "explanation": explanation
            }
    
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """자연어 태스크 실행"""
        if not self.connected or not self.page:
            success = await self.connect_to_browser()
            if not success:
                return {
                    "success": False,
                    "error": "브라우저에 연결할 수 없습니다."
                }
        
        try:
            # 현재 페이지 상태 수집
            screenshot_bytes = await self.playwright_controller.get_screenshot(self.page)
            interactive_rects = await self.playwright_controller.get_interactive_rects(self.page)
            visible_text = await self.playwright_controller.get_visible_text(self.page)
            
            # 인터랙티브 요소 정보 준비
            interactive_elements = []
            for element_id, rect_info in interactive_rects.items():
                interactive_elements.append({
                    "id": int(element_id),
                    "name": rect_info.get("name", ""),
                    "role": rect_info.get("role", ""),
                    "text": rect_info.get("text", ""),
                    "tag_name": rect_info.get("tag_name", "")
                })
            
            # 스크린샷에 요소 마커 추가
            marked_screenshot = add_element_markers(screenshot_bytes, interactive_rects)
            screenshot_b64 = base64.b64encode(marked_screenshot).decode('utf-8')
            
            # LLM으로 다음 액션 결정
            llm_response = self.get_llm_response(task, screenshot_b64, visible_text, interactive_elements)
            
            if not llm_response["success"]:
                return llm_response
            
            # 액션 실행
            action_result = await self.execute_action(llm_response["action"])
            
            # 결과에 페이지 정보 추가
            current_url = self.page.url if self.page else "unknown"
            current_title = await self.page.title() if self.page else "unknown"
            
            return {
                "success": True,
                "task": task,
                "action_taken": llm_response["action"],
                "action_result": action_result,
                "current_url": current_url,
                "current_title": current_title,
                "interactive_elements_count": len(interactive_elements),
                "screenshot_b64": screenshot_b64  # 디버깅용
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
            screenshot_bytes = await self.playwright_controller.get_screenshot(self.page)
            interactive_rects = await self.playwright_controller.get_interactive_rects(self.page)
            
            # 요소 마커 추가
            marked_screenshot = add_element_markers(screenshot_bytes, interactive_rects)
            screenshot_b64 = base64.b64encode(marked_screenshot).decode('utf-8')
            
            return {
                "success": True,
                "screenshot_b64": screenshot_b64,
                "current_url": self.page.url,
                "current_title": await self.page.title(),
                "interactive_elements_count": len(interactive_rects)
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
            interactive_rects = await self.playwright_controller.get_interactive_rects(self.page)
            visible_text = await self.playwright_controller.get_visible_text(self.page)
            
            return {
                "success": True,
                "url": self.page.url,
                "title": await self.page.title(),
                "connected": self.connected,
                "interactive_elements_count": len(interactive_rects),
                "visible_text_length": len(visible_text),
                "visible_text_preview": visible_text[:200] + "..." if len(visible_text) > 200 else visible_text
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# 전역 컨트롤러 인스턴스
controller = MagenticWebSurferController()

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "playwright_available": PLAYWRIGHT_AVAILABLE,
        "openai_available": OPENAI_AVAILABLE,
        "pil_available": PIL_AVAILABLE,
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
    print("🤖 Magentic UI WebSurfer Server 시작 중...")
    print("📋 사용 가능한 엔드포인트:")
    print("  - GET  /health       - 헬스 체크")
    print("  - POST /connect      - 브라우저 연결")
    print("  - POST /execute      - 자연어 태스크 실행")
    print("  - POST /screenshot   - 스크린샷 촬영")
    print("  - GET  /page_info    - 페이지 정보 조회")
    print("  - GET  /tasks/examples - 태스크 예시 목록")
    print()
    
    missing_deps = []
    if not PLAYWRIGHT_AVAILABLE:
        missing_deps.append("playwright")
    if not OPENAI_AVAILABLE:
        missing_deps.append("openai")
    if not PIL_AVAILABLE:
        missing_deps.append("Pillow")
    
    if missing_deps:
        print("⚠️  누락된 의존성:")
        for dep in missing_deps:
            print(f"   pip install {dep}")
        print()
    
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   export OPENAI_API_KEY='your-api-key'")
        print()
    
    # macOS AirPlay 충돌 방지를 위해 포트 5002 사용
    app.run(host='0.0.0.0', port=5002, debug=True)

