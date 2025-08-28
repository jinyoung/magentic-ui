#!/usr/bin/env python3
"""
Browser-Use Agent Executor for Magentic-UI
ProcessGPT SDK와 호환되는 AgentExecutor 형식의 browser-use 에이전트
"""

import asyncio
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Sequence, AsyncGenerator, Optional
from pathlib import Path

from pydantic import BaseModel, Field
from autogen_core import CancellationToken, ComponentModel, Component
from autogen_core.models import ChatCompletionClient
from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.state import BaseState
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    TextMessage,
    MessageFactory,
)

# browser-use 관련 임포트
try:
    from browser_use import Agent as BrowserUseAgent
    BROWSER_USE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: browser-use not available: {e}")
    BROWSER_USE_AVAILABLE = False

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
    model_context_token_limit: int = Field(default=128000, description="모델 컨텍스트 토큰 제한")


class BrowserUseAgentState(BaseState):
    """Browser-Use Agent 상태"""
    type: str = Field(default="BrowserUseAgentState")
    last_task: Optional[str] = Field(default=None, description="마지막 실행 태스크")
    last_result: Optional[Dict[str, Any]] = Field(default=None, description="마지막 실행 결과")
    execution_count: int = Field(default=0, description="실행 횟수")


class BrowserUseAgent(BaseChatAgent, Component[BrowserUseAgentConfig]):
    """
    Browser-Use를 활용한 웹 브라우저 자동화 에이전트
    
    자연어 태스크를 받아서 browser-use를 통해 웹 브라우저를 자동화하여 실행합니다.
    ProcessGPT SDK와 호환되는 AgentExecutor 패턴을 따릅니다.
    """
    
    component_type = "agent"
    component_config_schema = BrowserUseAgentConfig
    component_provider_override = "magentic_ui.agents.BrowserUseAgent"

    DEFAULT_DESCRIPTION = """
    웹 브라우저를 자동화하여 다양한 웹 태스크를 수행하는 에이전트입니다.
    자연어로 지시한 브라우저 작업을 실행할 수 있습니다:
    - 웹사이트 방문 및 탐색
    - 검색 및 정보 수집
    - 폼 작성 및 제출
    - 웹페이지 상호작용
    """

    def __init__(
        self,
        name: str,
        model_client: ChatCompletionClient,
        description: str = DEFAULT_DESCRIPTION,
        config: Optional[BrowserUseAgentConfig] = None,
    ) -> None:
        """Browser-Use Agent 초기화"""
        super().__init__(name, description)
        self._model_client = model_client
        self._config = config or BrowserUseAgentConfig()
        self._state = BrowserUseAgentState()
        self._browser_agent: Optional[BrowserUseAgent] = None
        
        # 환경 설정
        if not BROWSER_USE_AVAILABLE:
            logger.warning("browser-use가 설치되지 않았습니다. pip install browser-use로 설치하세요.")

    async def execute_task(self, task: str) -> Dict[str, Any]:
        """
        자연어 태스크를 browser-use를 통해 실행
        
        Args:
            task: 실행할 자연어 태스크 (예: "Google에서 'playwright' 검색하기")
            
        Returns:
            실행 결과를 포함한 딕셔너리
        """
        if not BROWSER_USE_AVAILABLE:
            return {
                "success": False,
                "error": "browser-use가 설치되지 않았습니다.",
                "task": task
            }

        try:
            logger.info(f"브라우저 태스크 실행 시작: {task}")
            
            # browser-use Agent 생성
            self._browser_agent = BrowserUseAgent(
                task=task,
                llm_model=self._config.llm_model,
                headless=self._config.headless,
                save_recording_path=self._config.save_recording_path,
                max_actions=self._config.max_actions,
                include_attributes=self._config.include_attributes,
            )
            
            # 태스크 실행
            result = await self._browser_agent.run()
            
            # 상태 업데이트
            self._state.last_task = task
            self._state.execution_count += 1
            self._state.last_result = {
                "success": True,
                "result": str(result),
                "task": task,
                "timestamp": datetime.now().isoformat(),
                "execution_count": self._state.execution_count
            }
            
            logger.info(f"브라우저 태스크 실행 완료: {task}")
            return self._state.last_result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "task": task,
                "timestamp": datetime.now().isoformat(),
                "execution_count": self._state.execution_count
            }
            
            self._state.last_result = error_result
            logger.error(f"브라우저 태스크 실행 실패: {e}")
            return error_result

    async def on_messages_stream(
        self,
        messages: Sequence[BaseChatMessage],
        cancellation_token: CancellationToken,
    ) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]:
        """메시지 스트림 처리"""
        
        # 마지막 메시지에서 태스크 추출
        if not messages:
            yield TextMessage(
                content="태스크가 제공되지 않았습니다.",
                source=self.name
            )
            return

        last_message = messages[-1]
        if isinstance(last_message, TextMessage):
            task = last_message.content
            
            # 태스크 실행
            result = await self.execute_task(task)
            
            if result["success"]:
                response_content = f"브라우저 태스크 '{task}'를 성공적으로 실행했습니다.\n\n결과: {result['result']}"
            else:
                response_content = f"브라우저 태스크 '{task}' 실행 중 오류가 발생했습니다.\n\n오류: {result['error']}"
                
            yield TextMessage(
                content=response_content,
                source=self.name
            )
        else:
            yield TextMessage(
                content="텍스트 메시지만 처리할 수 있습니다.",
                source=self.name
            )

    async def on_messages(
        self,
        messages: Sequence[BaseChatMessage],
        cancellation_token: CancellationToken,
    ) -> Response:
        """메시지 처리 (스트림이 아닌 경우)"""
        
        response_messages: List[BaseChatMessage] = []
        async for message in self.on_messages_stream(messages, cancellation_token):
            if isinstance(message, BaseChatMessage):
                response_messages.append(message)
                
        return Response(chat_message=response_messages[-1] if response_messages else None)

    def get_state(self) -> BrowserUseAgentState:
        """현재 상태 반환"""
        return self._state

    def reset_state(self) -> None:
        """상태 초기화"""
        self._state = BrowserUseAgentState()
        self._browser_agent = None


# AgentExecutor 호환 클래스
class BrowserUseAgentExecutor:
    """
    ProcessGPT SDK와 호환되는 AgentExecutor 인터페이스
    """
    
    def __init__(self, agent: BrowserUseAgent):
        self.agent = agent
        
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """태스크 실행"""
        return await self.agent.execute_task(task)
        
    def get_status(self) -> Dict[str, Any]:
        """실행기 상태 반환"""
        state = self.agent.get_state()
        return {
            "agent_name": self.agent.name,
            "browser_use_available": BROWSER_USE_AVAILABLE,
            "execution_count": state.execution_count,
            "last_task": state.last_task,
            "last_result": state.last_result,
            "timestamp": datetime.now().isoformat()
        }
