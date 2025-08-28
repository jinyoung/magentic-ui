#!/usr/bin/env python3
"""
Integrated Browser-Use Server with ProcessGPT Agent Support
통합된 브라우저-사용 서버 - ProcessGPT Agent Server와 호환
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Sequence, AsyncGenerator
import traceback
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS
import nest_asyncio

# Pydantic 모델 및 기본 타입
from pydantic import BaseModel, Field

# browser-use 관련 임포트
try:
    from browser_use import Agent as BrowserUseAgent
    BROWSER_USE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: browser-use not available: {e}")
    BROWSER_USE_AVAILABLE = False

# ProcessGPT SDK 임포트 시도
try:
    from processgpt_agent_sdk.simulator import ProcessGPTAgentSimulator
    from processgpt_agent_sdk.server import ProcessGPTAgentServer
    PROCESSGPT_SDK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ProcessGPT SDK not available: {e}")
    PROCESSGPT_SDK_AVAILABLE = False

# Flask 앱 설정
app = Flask(__name__)
CORS(app)
nest_asyncio.apply()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrowserUseAgentConfig(BaseModel):
    """Browser-Use Agent 설정"""
    llm_model: str = Field(default="gpt-4o-mini", description="사용할 LLM 모델")
    headless: bool = Field(default=False, description="헤드리스 모드 실행 여부")
    save_recording_path: Optional[str] = Field(default=None, description="녹화 저장 경로")
    max_actions: int = Field(default=100, description="최대 액션 수")
    include_attributes: List[str] = Field(
        default_factory=lambda: ["title", "type", "name", "role"], 
        description="포함할 HTML 속성들"
    )
    display: str = Field(default=":99", description="X11 디스플레이")


class BrowserUseAgentState(BaseModel):
    """Browser-Use Agent 상태"""
    last_task: Optional[str] = Field(default=None, description="마지막 실행 태스크")
    last_result: Optional[Dict[str, Any]] = Field(default=None, description="마지막 실행 결과")
    execution_count: int = Field(default=0, description="실행 횟수")
    browser_active: bool = Field(default=False, description="브라우저 활성 상태")


class SharedBrowserSession:
    """공유 브라우저 세션 관리"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.context = None
        self.is_initialized = False
        
    async def get_or_create_browser(self):
        """브라우저 인스턴스를 가져오거나 생성"""
        if not self.is_initialized:
            # browser-use가 내부적으로 브라우저를 관리하므로
            # 여기서는 세션 정보만 추적
            self.is_initialized = True
            logger.info("브라우저 세션 초기화됨")
        return self.browser
        
    async def close(self):
        """브라우저 세션 종료"""
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
        self.is_initialized = False
        logger.info("브라우저 세션 종료됨")


class IntegratedBrowserController:
    """통합된 브라우저 컨트롤러 - ProcessGPT AgentExecutor 패턴 구현"""
    
    def __init__(self, config: Optional[BrowserUseAgentConfig] = None):
        self.config = config or BrowserUseAgentConfig()
        self.state = BrowserUseAgentState()
        self.browser_session = SharedBrowserSession()
        self.current_agent: Optional[BrowserUseAgent] = None
        
        # 환경 설정
        os.environ['DISPLAY'] = self.config.display
        logger.info(f"브라우저 컨트롤러 초기화됨 (DISPLAY={self.config.display})")

    async def execute_task(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        자연어 태스크를 browser-use를 통해 실행
        ProcessGPT AgentExecutor 인터페이스 호환
        """
        if not BROWSER_USE_AVAILABLE:
            return {
                "success": False,
                "error": "browser-use가 설치되지 않았습니다.",
                "task": task
            }

        try:
            logger.info(f"브라우저 태스크 실행 시작: {task}")
            
            # 공유 브라우저 세션 준비
            await self.browser_session.get_or_create_browser()
            
            # browser-use Agent 생성 (기존 브라우저 세션 활용 시도)
            agent_kwargs = {
                "task": task,
                "llm_model": self.config.llm_model,
                "headless": self.config.headless,
                "max_actions": self.config.max_actions,
                "include_attributes": self.config.include_attributes,
            }
            
            # 녹화 경로 설정
            if self.config.save_recording_path:
                agent_kwargs["save_recording_path"] = self.config.save_recording_path
                
            self.current_agent = BrowserUseAgent(**agent_kwargs)
            
            # 태스크 실행
            result = await self.current_agent.run()
            
            # 상태 업데이트
            self.state.last_task = task
            self.state.execution_count += 1
            self.state.browser_active = True
            self.state.last_result = {
                "success": True,
                "result": str(result),
                "task": task,
                "timestamp": datetime.now().isoformat(),
                "execution_count": self.state.execution_count
            }
            
            logger.info(f"브라우저 태스크 실행 완료: {task}")
            return self.state.last_result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "task": task,
                "timestamp": datetime.now().isoformat(),
                "execution_count": self.state.execution_count
            }
            
            self.state.last_result = error_result
            logger.error(f"브라우저 태스크 실행 실패: {e}")
            return error_result

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        return {
            "success": True,
            "browser_use_available": BROWSER_USE_AVAILABLE,
            "processgpt_sdk_available": PROCESSGPT_SDK_AVAILABLE,
            "agent_active": self.current_agent is not None,
            "browser_active": self.state.browser_active,
            "execution_count": self.state.execution_count,
            "last_task": self.state.last_task,
            "last_result": self.state.last_result,
            "timestamp": datetime.now().isoformat(),
            "display": os.environ.get('DISPLAY', 'not_set'),
            "config": self.config.model_dump()
        }

    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """ProcessGPT AgentExecutor 호환 메서드"""
        return await self.execute_task(task, **kwargs)

    async def close(self):
        """리소스 정리"""
        await self.browser_session.close()
        self.current_agent = None
        self.state.browser_active = False


# 전역 컨트롤러 인스턴스
controller = IntegratedBrowserController()


class ProcessGPTBrowserAgentServer:
    """ProcessGPT AgentServer 호환 브라우저 에이전트 서버"""
    
    def __init__(self, controller: IntegratedBrowserController):
        self.controller = controller
        self.is_running = False
        
    async def start(self):
        """서버 시작"""
        self.is_running = True
        logger.info("ProcessGPT Browser Agent Server 시작됨")
        
    async def stop(self):
        """서버 중지"""
        await self.controller.close()
        self.is_running = False
        logger.info("ProcessGPT Browser Agent Server 중지됨")
        
    async def execute_task(self, task: str, **kwargs) -> Dict[str, Any]:
        """태스크 실행"""
        return await self.controller.execute_task(task, **kwargs)
        
    def get_status(self) -> Dict[str, Any]:
        """서버 상태"""
        status = self.controller.get_status()
        status["server_running"] = self.is_running
        return status


# ProcessGPT 서버 인스턴스
processgpt_server = ProcessGPTBrowserAgentServer(controller)


# === Flask 라우트 정의 ===

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "browser_use_available": BROWSER_USE_AVAILABLE,
        "processgpt_sdk_available": PROCESSGPT_SDK_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
        "environment": "docker_container"
    })


@app.route('/status', methods=['GET'])
def get_status():
    """상태 조회"""
    return jsonify(processgpt_server.get_status())


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
    kwargs = data.get('kwargs', {})
    
    # 새로운 이벤트 루프 생성
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(controller.execute_task(task, **kwargs))
        return jsonify(result)
    finally:
        loop.close()


@app.route('/tasks/examples', methods=['GET'])
def get_task_examples():
    """태스크 예시 목록"""
    examples = [
        {
            "title": "구글 검색 - Playwright",
            "task": "Google에서 'playwright' 검색하기",
            "description": "구글에서 Playwright 관련 검색을 수행합니다"
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
            "title": "폼 작성 및 검색",
            "task": "검색창에 'browser automation' 입력하고 검색하기",
            "description": "웹 폼에 텍스트를 입력하고 제출합니다"
        },
        {
            "title": "페이지 네비게이션",
            "task": "첫 번째 검색 결과 클릭하고 페이지 내용 확인하기",
            "description": "검색 결과를 클릭하여 상세 페이지로 이동합니다"
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
        "message": "Integrated Browser-Use ProcessGPT Server가 정상적으로 실행 중입니다!",
        "timestamp": datetime.now().isoformat(),
        "environment_info": {
            "display": os.environ.get('DISPLAY'),
            "python_path": os.environ.get('PATH'),
            "browser_use_available": BROWSER_USE_AVAILABLE,
            "processgpt_sdk_available": PROCESSGPT_SDK_AVAILABLE
        }
    })


@app.route('/processgpt/execute', methods=['POST'])
def processgpt_execute():
    """ProcessGPT 호환 실행 엔드포인트"""
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "error": "요청 데이터가 없습니다."
        }), 400
        
    # ProcessGPT 형식에 맞춰 파라미터 추출
    task = data.get('task') or data.get('command')
    if not task:
        return jsonify({
            "success": False,
            "error": "task 또는 command가 제공되지 않았습니다."
        }), 400
    
    kwargs = data.get('parameters', {})
    
    # 이벤트 루프에서 실행
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(processgpt_server.execute_task(task, **kwargs))
        return jsonify(result)
    finally:
        loop.close()


async def start_processgpt_server():
    """ProcessGPT 서버 시작"""
    try:
        await processgpt_server.start()
        logger.info("ProcessGPT Browser Agent Server 준비 완료")
    except Exception as e:
        logger.error(f"ProcessGPT 서버 시작 실패: {e}")


async def main():
    """메인 실행 함수"""
    print("🚀 Integrated Browser-Use ProcessGPT Server 시작 중...")
    print("=" * 60)
    print("📋 사용 가능한 엔드포인트:")
    print("  - GET  /health              - 헬스 체크")
    print("  - GET  /status              - 상태 조회")
    print("  - POST /execute             - 자연어 태스크 실행")
    print("  - POST /processgpt/execute  - ProcessGPT 호환 실행")
    print("  - GET  /tasks/examples      - 태스크 예시 목록")
    print("  - GET  /test                - 테스트 엔드포인트")
    print()
    
    if not BROWSER_USE_AVAILABLE:
        print("⚠️  browser-use가 설치되지 않았습니다.")
    else:
        print("✅ browser-use 사용 가능")
        
    if not PROCESSGPT_SDK_AVAILABLE:
        print("⚠️  ProcessGPT SDK가 설치되지 않았습니다.")
    else:
        print("✅ ProcessGPT SDK 사용 가능")
    
    print()
    
    # ProcessGPT 서버 시작
    await start_processgpt_server()
    
    # Flask 서버 시작
    print("🌐 Flask 서버 시작 (0.0.0.0:5001)")
    app.run(host='0.0.0.0', port=5001, debug=False)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 서버 종료 중...")
        # 정리 작업
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(processgpt_server.stop())
        loop.close()
        print("✅ 서버 종료 완료")
