#!/usr/bin/env python3
"""
Browser-Use AgentExecutor for ProcessGPT SDK
ProcessGPT SDK의 AgentExecutor 인터페이스를 구현한 브라우저 자동화 에이전트
"""

import asyncio
import os
import logging
from datetime import datetime
from typing import Any, Dict, Optional
import traceback

# ProcessGPT SDK imports
try:
    from a2a.server.agent_execution import AgentExecutor, RequestContext
    from a2a.server.events import EventQueue, Event
    PROCESSGPT_SDK_AVAILABLE = True
except ImportError:
    # Fallback classes for when SDK is not available
    class AgentExecutor:
        async def execute(self, context, event_queue): pass
        async def cancel(self, context, event_queue): pass
    
    class RequestContext:
        def get_user_input(self): return ""
        def get_context_data(self): return {}
    
    class EventQueue:
        def enqueue_event(self, event): pass
    
    class Event:
        def __init__(self, type, data): 
            self.type = type
            self.data = data
    
    PROCESSGPT_SDK_AVAILABLE = False
    print("Warning: ProcessGPT SDK not available. Using fallback classes.")

# browser-use imports
try:
    from browser_use import Agent as BrowserUseAgent
    BROWSER_USE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: browser-use not available: {e}")
    BROWSER_USE_AVAILABLE = False

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrowserUseAgentExecutor(AgentExecutor):
    """
    ProcessGPT SDK와 호환되는 Browser-Use AgentExecutor
    웹 브라우저 자동화 작업을 처리하는 에이전트 실행기
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Browser-Use AgentExecutor 초기화
        
        Args:
            config: 설정 딕셔너리
                - llm_model: 사용할 LLM 모델 (기본: gpt-4o-mini)
                - headless: 헤드리스 모드 여부 (기본: False)
                - max_actions: 최대 액션 수 (기본: 50)
                - save_recording_path: 녹화 저장 경로
                - timeout: 작업 타임아웃 (초)
        """
        self.config = config or {}
        self.is_cancelled = False
        self.browser_agent: Optional[BrowserUseAgent] = None
        
        # 기본 설정값
        self.llm_model = self.config.get('llm_model', 'gpt-4o-mini')
        self.headless = self.config.get('headless', False)
        self.max_actions = self.config.get('max_actions', 50)
        self.save_recording_path = self.config.get('save_recording_path', None)
        self.timeout = self.config.get('timeout', 120)  # 2분 기본 타임아웃
        
        # 환경 설정
        self._setup_environment()
        
        logger.info(f"BrowserUseAgentExecutor 초기화됨 - 모델: {self.llm_model}, 헤드리스: {self.headless}")

    def _setup_environment(self):
        """환경변수 설정"""
        # DISPLAY 환경변수 설정 (Docker 환경)
        if not os.getenv('DISPLAY'):
            os.environ['DISPLAY'] = ':99'
        
        logger.info(f"DISPLAY 설정: {os.environ.get('DISPLAY')}")

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        메인 실행 로직 - ProcessGPT SDK 인터페이스 구현
        
        Args:
            context: 요청 컨텍스트 (사용자 입력, 컨텍스트 데이터 포함)
            event_queue: 이벤트 큐 (진행 상황 및 결과 전송용)
        """
        # 사용자 입력 가져오기
        user_input = context.get_user_input()
        context_data = context.get_context_data()
        
        logger.info(f"브라우저 태스크 시작: {user_input}")
        
        # 시작 이벤트 발송
        start_event = Event(
            type="task_started",
            data={
                "message": f"🚀 브라우저 작업 시작: {user_input}",
                "user_input": user_input,
                "agent_type": "BrowserUseAgent",
                "config": {
                    "llm_model": self.llm_model,
                    "headless": self.headless,
                    "max_actions": self.max_actions
                }
            }
        )
        event_queue.enqueue_event(start_event)
        
        if not BROWSER_USE_AVAILABLE:
            error_event = Event(
                type="error",
                data={
                    "message": "❌ browser-use 패키지가 설치되지 않았습니다.",
                    "error": "browser-use package not installed",
                    "solution": "pip install browser-use 로 설치하세요."
                }
            )
            event_queue.enqueue_event(error_event)
            return
        
        try:
            # 브라우저 작업 단계별 처리
            await self._process_browser_task(user_input, context_data, event_queue)
            
            # 성공 완료 이벤트
            if not self.is_cancelled:
                success_event = Event(
                    type="done",
                    data={
                        "message": "✅ 브라우저 작업이 성공적으로 완료되었습니다",
                        "success": True,
                        "completed_at": datetime.now().isoformat()
                    }
                )
                event_queue.enqueue_event(success_event)
                
        except Exception as e:
            logger.error(f"브라우저 작업 실행 중 오류: {e}")
            error_event = Event(
                type="error",
                data={
                    "message": f"❌ 브라우저 작업 처리 중 오류 발생: {str(e)}",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            )
            event_queue.enqueue_event(error_event)
            raise

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        작업 취소 처리
        
        Args:
            context: 요청 컨텍스트
            event_queue: 이벤트 큐
        """
        logger.info("브라우저 작업 취소 요청")
        self.is_cancelled = True
        
        # 브라우저 에이전트가 실행 중이면 중지 시도
        if self.browser_agent:
            try:
                # browser-use Agent는 직접 취소 메서드가 없으므로
                # 플래그만 설정하고 다음 체크포인트에서 중지
                logger.info("브라우저 에이전트 취소 플래그 설정")
            except Exception as e:
                logger.warning(f"브라우저 에이전트 취소 중 오류: {e}")
        
        cancel_event = Event(
            type="cancelled",
            data={
                "message": "🛑 브라우저 작업이 취소되었습니다",
                "cancelled_by": "user_request",
                "cancelled_at": datetime.now().isoformat()
            }
        )
        event_queue.enqueue_event(cancel_event)

    async def _process_browser_task(self, user_input: str, context_data: Dict[str, Any], event_queue: EventQueue):
        """
        실제 브라우저 작업 처리
        
        Args:
            user_input: 사용자가 입력한 태스크
            context_data: 추가 컨텍스트 데이터
            event_queue: 이벤트 큐
        """
        # 진행 단계 정의
        steps = [
            ("초기화", "브라우저 에이전트를 초기화하고 있습니다..."),
            ("설정", "브라우저 설정을 구성하고 있습니다..."),
            ("실행", f"'{user_input}' 작업을 실행하고 있습니다..."),
            ("완료", "결과를 처리하고 있습니다...")
        ]
        
        for i, (step_name, step_message) in enumerate(steps, 1):
            if self.is_cancelled:
                logger.info(f"작업이 취소됨 - 단계 {i}")
                break
            
            # 진행 상황 이벤트
            progress_event = Event(
                type="progress",
                data={
                    "step": i,
                    "total_steps": len(steps),
                    "step_name": step_name,
                    "message": step_message,
                    "progress_percentage": (i / len(steps)) * 100
                }
            )
            event_queue.enqueue_event(progress_event)
            
            if i == 3:  # 실행 단계
                # 실제 browser-use 에이전트 실행
                result = await self._execute_browser_use_agent(user_input, event_queue)
                
                # 결과 출력 이벤트
                output_event = Event(
                    type="output",
                    data={
                        "content": result,
                        "task": user_input,
                        "final": True
                    }
                )
                event_queue.enqueue_event(output_event)
            else:
                # 시뮬레이션용 짧은 지연
                await asyncio.sleep(1.0)

    async def _execute_browser_use_agent(self, task: str, event_queue: EventQueue) -> Dict[str, Any]:
        """
        browser-use 에이전트 실행
        
        Args:
            task: 실행할 태스크
            event_queue: 이벤트 큐
            
        Returns:
            실행 결과 딕셔너리
        """
        try:
            # browser-use Agent 생성
            agent_kwargs = {
                "task": task,
                "llm_model": self.llm_model,
                "headless": self.headless,
                "max_actions": self.max_actions,
                "include_attributes": ["title", "type", "name", "role", "aria-label"]
            }
            
            # 녹화 경로 설정
            if self.save_recording_path:
                agent_kwargs["save_recording_path"] = self.save_recording_path
                
            self.browser_agent = BrowserUseAgent(**agent_kwargs)
            
            # 에이전트 생성 완료 이벤트
            agent_created_event = Event(
                type="progress",
                data={
                    "message": f"🌐 브라우저 에이전트 생성 완료 (모델: {self.llm_model})",
                    "agent_ready": True
                }
            )
            event_queue.enqueue_event(agent_created_event)
            
            # 타임아웃과 함께 태스크 실행
            try:
                result = await asyncio.wait_for(
                    self.browser_agent.run(),
                    timeout=self.timeout
                )
                
                return {
                    "success": True,
                    "result": str(result),
                    "task": task,
                    "timestamp": datetime.now().isoformat(),
                    "agent_config": {
                        "llm_model": self.llm_model,
                        "headless": self.headless,
                        "max_actions": self.max_actions
                    }
                }
                
            except asyncio.TimeoutError:
                timeout_msg = f"브라우저 작업이 {self.timeout}초 타임아웃으로 인해 중단되었습니다."
                logger.warning(timeout_msg)
                
                timeout_event = Event(
                    type="warning",
                    data={
                        "message": f"⏰ {timeout_msg}",
                        "timeout": self.timeout
                    }
                )
                event_queue.enqueue_event(timeout_event)
                
                return {
                    "success": False,
                    "error": "timeout",
                    "message": timeout_msg,
                    "task": task,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            error_msg = f"브라우저 에이전트 실행 중 오류: {str(e)}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "error": str(e),
                "message": error_msg,
                "task": task,
                "timestamp": datetime.now().isoformat(),
                "traceback": traceback.format_exc()
            }

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 반환"""
        return {
            "agent_type": "BrowserUseAgentExecutor",
            "browser_use_available": BROWSER_USE_AVAILABLE,
            "processgpt_sdk_available": PROCESSGPT_SDK_AVAILABLE,
            "is_cancelled": self.is_cancelled,
            "agent_active": self.browser_agent is not None,
            "config": {
                "llm_model": self.llm_model,
                "headless": self.headless,
                "max_actions": self.max_actions,
                "timeout": self.timeout
            },
            "environment": {
                "display": os.environ.get('DISPLAY'),
                "openai_api_key_set": bool(os.getenv('OPENAI_API_KEY'))
            },
            "timestamp": datetime.now().isoformat()
        }
