#!/usr/bin/env python3
"""
Browser-Use Agent Test with ProcessGPTAgentSimulator
ProcessGPTAgentSimulator를 사용하여 browser-use 에이전트를 테스트합니다.
"""

import asyncio
import os
import logging
from datetime import datetime
from typing import Dict, Any

# ProcessGPT SDK 임포트
try:
    from processgpt_agent_sdk.simulator import ProcessGPTAgentSimulator
    PROCESSGPT_SDK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ProcessGPT SDK not available: {e}")
    print("pip install processgpt-agent-sdk 로 설치하세요.")
    PROCESSGPT_SDK_AVAILABLE = False

# Autogen 관련 임포트
from autogen_core.models import OpenAIChatCompletionClient
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

# 프로젝트 내부 임포트
from src.magentic_ui.agents.browser_use_agent import (
    BrowserUseAgent, 
    BrowserUseAgentExecutor, 
    BrowserUseAgentConfig
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrowserUseTestRunner:
    """Browser-Use Agent 테스트 실행기"""
    
    def __init__(self):
        self.model_client = None
        self.agent = None
        self.executor = None
        
    async def setup(self):
        """테스트 환경 설정"""
        # OpenAI API 키 확인
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        
        # 모델 클라이언트 생성
        self.model_client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Browser-Use Agent 설정
        config = BrowserUseAgentConfig(
            llm_model="gpt-4o-mini",
            headless=False,  # GUI 모드로 실행하여 동작을 확인
            max_actions=20,
            save_recording_path="./test_recording"
        )
        
        # Browser-Use Agent 생성
        self.agent = BrowserUseAgent(
            name="test_browser_agent",
            model_client=self.model_client,
            config=config
        )
        
        # AgentExecutor 생성
        self.executor = BrowserUseAgentExecutor(self.agent)
        
        logger.info("테스트 환경 설정 완료")

    async def test_google_search_playwright(self):
        """Google에서 'playwright' 검색 테스트"""
        logger.info("Google 'playwright' 검색 테스트 시작")
        
        task = "Google에서 'playwright' 검색하기"
        
        try:
            # 직접 실행 테스트
            result = await self.executor.execute(task)
            
            print(f"\n=== 테스트 결과 ===")
            print(f"태스크: {task}")
            print(f"성공 여부: {result['success']}")
            if result['success']:
                print(f"결과: {result['result']}")
            else:
                print(f"오류: {result['error']}")
            print(f"실행 시간: {result['timestamp']}")
            
            return result
            
        except Exception as e:
            logger.error(f"테스트 실행 중 오류: {e}")
            return {"success": False, "error": str(e)}

    async def test_with_agent_messages(self):
        """Agent 메시지 인터페이스 테스트"""
        logger.info("Agent 메시지 인터페이스 테스트 시작")
        
        task_message = TextMessage(
            content="Google에서 'playwright' 검색하고 첫 번째 결과 클릭하기",
            source="user"
        )
        
        try:
            response = await self.agent.on_messages(
                messages=[task_message],
                cancellation_token=CancellationToken()
            )
            
            print(f"\n=== Agent 메시지 테스트 결과 ===")
            if response.chat_message:
                print(f"응답: {response.chat_message.content}")
            else:
                print("응답이 없습니다.")
                
            return response
            
        except Exception as e:
            logger.error(f"Agent 메시지 테스트 중 오류: {e}")
            return None

    async def test_with_processgpt_simulator(self):
        """ProcessGPTAgentSimulator를 사용한 테스트"""
        if not PROCESSGPT_SDK_AVAILABLE:
            print("ProcessGPT SDK가 설치되지 않아 시뮬레이터 테스트를 건너뜁니다.")
            return None
            
        logger.info("ProcessGPTAgentSimulator 테스트 시작")
        
        try:
            # ProcessGPTAgentSimulator 설정
            simulator = ProcessGPTAgentSimulator()
            
            # 에이전트 등록
            simulator.register_agent('browser_agent', self.executor)
            
            # 테스트 실행
            result = simulator.run_agent(
                'browser_agent', 
                command='execute',
                task="Google에서 'playwright' 검색하기"
            )
            
            print(f"\n=== ProcessGPT Simulator 테스트 결과 ===")
            print(f"결과: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"ProcessGPT Simulator 테스트 중 오류: {e}")
            return None

    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 Browser-Use Agent 테스트 시작")
        print("=" * 50)
        
        try:
            # 환경 설정
            await self.setup()
            
            # 테스트 실행
            test1_result = await self.test_google_search_playwright()
            test2_result = await self.test_with_agent_messages()
            test3_result = await self.test_with_processgpt_simulator()
            
            # 최종 상태 출력
            status = self.executor.get_status()
            print(f"\n=== 최종 상태 ===")
            print(f"에이전트: {status['agent_name']}")
            print(f"Browser-Use 사용 가능: {status['browser_use_available']}")
            print(f"실행 횟수: {status['execution_count']}")
            print(f"마지막 태스크: {status['last_task']}")
            
            print("\n✅ 모든 테스트 완료")
            
        except Exception as e:
            logger.error(f"테스트 실행 중 오류: {e}")
            print(f"\n❌ 테스트 실패: {e}")
        
        finally:
            # 리소스 정리
            if self.model_client:
                await self.model_client.close()


async def main():
    """메인 실행 함수"""
    runner = BrowserUseTestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    # 사용법 출력
    print("Browser-Use Agent Test with ProcessGPTAgentSimulator")
    print("=" * 60)
    print("이 테스트는 다음을 수행합니다:")
    print("1. Browser-Use Agent 설정 및 초기화")
    print("2. Google에서 'playwright' 검색 테스트")
    print("3. Agent 메시지 인터페이스 테스트")
    print("4. ProcessGPTAgentSimulator 테스트 (SDK 설치된 경우)")
    print()
    print("요구사항:")
    print("- OPENAI_API_KEY 환경변수 설정")
    print("- browser-use 패키지 설치 (pip install browser-use)")
    print("- playwright 설치 (playwright install)")
    print("- processgpt-agent-sdk 설치 (선택사항)")
    print()
    
    # 환경변수 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경변수를 설정해주세요.")
        exit(1)
    
    # 테스트 실행
    asyncio.run(main())
