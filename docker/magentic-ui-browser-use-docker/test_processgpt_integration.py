#!/usr/bin/env python3
"""
ProcessGPT Integration Test
ProcessGPT SDK와 Browser-Use 통합 테스트
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from browser_use_agent_executor import BrowserUseAgentExecutor


class MockRequestContext:
    """테스트용 RequestContext 모의 객체"""
    
    def __init__(self, user_input: str, context_data: dict = None):
        self.user_input = user_input
        self.context_data = context_data or {}
    
    def get_user_input(self) -> str:
        return self.user_input
    
    def get_context_data(self) -> dict:
        return self.context_data


class MockEventQueue:
    """테스트용 EventQueue 모의 객체"""
    
    def __init__(self):
        self.events = []
    
    def enqueue_event(self, event):
        self.events.append(event)
        print(f"📨 이벤트: {event.type} - {event.data.get('message', '')}")
    
    def get_events(self):
        return self.events
    
    def clear(self):
        self.events.clear()


class MockEvent:
    """테스트용 Event 모의 객체"""
    
    def __init__(self, type: str, data: dict):
        self.type = type
        self.data = data


# Mock 클래스들을 전역으로 등록
import browser_use_agent_executor
browser_use_agent_executor.Event = MockEvent


async def test_browser_agent_executor():
    """BrowserUseAgentExecutor 직접 테스트"""
    print("🧪 BrowserUseAgentExecutor 직접 테스트")
    print("=" * 50)
    
    # AgentExecutor 설정
    config = {
        "llm_model": "gpt-4o-mini",
        "headless": True,  # 테스트이므로 헤드리스 모드
        "max_actions": 10,
        "timeout": 60
    }
    
    # AgentExecutor 생성
    executor = BrowserUseAgentExecutor(config=config)
    
    # 상태 확인
    status = executor.get_status()
    print("📊 초기 상태:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    print()
    
    # 테스트 케이스들
    test_cases = [
        "Google 홈페이지 방문하기",
        "네이버에서 '날씨' 검색하기",
        "GitHub 홈페이지로 이동하기"
    ]
    
    for i, task in enumerate(test_cases, 1):
        print(f"🔍 테스트 {i}: {task}")
        print("-" * 30)
        
        # 모의 객체 생성
        context = MockRequestContext(user_input=task)
        event_queue = MockEventQueue()
        
        start_time = datetime.now()
        
        try:
            # AgentExecutor 실행
            await executor.execute(context, event_queue)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"✅ 테스트 완료 (소요시간: {duration:.2f}초)")
            print(f"📊 발생한 이벤트 수: {len(event_queue.get_events())}")
            
            # 마지막 이벤트 확인
            events = event_queue.get_events()
            if events:
                last_event = events[-1]
                print(f"🔚 마지막 이벤트: {last_event.type}")
                if last_event.type == "done":
                    print("✅ 작업 성공적으로 완료")
                elif last_event.type == "error":
                    print("❌ 작업 실행 중 오류 발생")
            
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
        
        print()


async def test_browser_agent_without_api_key():
    """API 키 없이 AgentExecutor 테스트 (상태 확인만)"""
    print("🔐 API 키 없이 상태 확인 테스트")
    print("=" * 40)
    
    # 임시로 API 키 제거
    original_api_key = os.getenv("OPENAI_API_KEY")
    if original_api_key:
        del os.environ["OPENAI_API_KEY"]
    
    try:
        executor = BrowserUseAgentExecutor()
        status = executor.get_status()
        
        print("📊 시스템 상태 (API 키 없음):")
        for key, value in status.items():
            if key == "environment":
                print(f"  {key}:")
                for env_key, env_value in value.items():
                    print(f"    {env_key}: {env_value}")
            else:
                print(f"  {key}: {value}")
        
        # 간단한 실행 테스트 (실패 예상)
        context = MockRequestContext("테스트 태스크")
        event_queue = MockEventQueue()
        
        try:
            await executor.execute(context, event_queue)
        except Exception as e:
            print(f"예상된 오류 (API 키 없음): {type(e).__name__}")
    
    finally:
        # API 키 복구
        if original_api_key:
            os.environ["OPENAI_API_KEY"] = original_api_key


async def test_cancel_functionality():
    """취소 기능 테스트"""
    print("🛑 취소 기능 테스트")
    print("=" * 30)
    
    executor = BrowserUseAgentExecutor()
    context = MockRequestContext("장시간 작업 테스트")
    event_queue = MockEventQueue()
    
    # 실행과 동시에 취소
    try:
        # 비동기적으로 취소 실행
        async def cancel_after_delay():
            await asyncio.sleep(2)  # 2초 후 취소
            await executor.cancel(context, event_queue)
        
        # 실행과 취소를 동시에 시작
        execution_task = asyncio.create_task(executor.execute(context, event_queue))
        cancel_task = asyncio.create_task(cancel_after_delay())
        
        # 두 작업 완료 대기
        await asyncio.gather(execution_task, cancel_task, return_exceptions=True)
        
        # 이벤트 확인
        events = event_queue.get_events()
        has_cancel_event = any(event.type == "cancelled" for event in events)
        
        if has_cancel_event:
            print("✅ 취소 기능 정상 작동")
        else:
            print("⚠️ 취소 이벤트가 발생하지 않음")
            
    except Exception as e:
        print(f"❌ 취소 테스트 실패: {e}")


def check_environment():
    """환경 확인"""
    print("🔍 환경 확인")
    print("=" * 20)
    
    # Python 버전
    print(f"Python 버전: {sys.version}")
    
    # 필수 패키지 확인
    packages_to_check = [
        "browser_use",
        "playwright",
        "openai",
        "pydantic"
    ]
    
    print("\n📦 패키지 확인:")
    for package in packages_to_check:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (설치되지 않음)")
    
    # 환경변수 확인
    print("\n🔑 환경변수 확인:")
    env_vars = [
        "OPENAI_API_KEY",
        "DISPLAY",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # API 키는 부분적으로만 표시
            if "KEY" in var:
                display_value = f"{value[:10]}...({len(value)}자)"
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: 설정되지 않음")
    
    print()


async def main():
    """메인 테스트 함수"""
    print("🌟 ProcessGPT Browser-Use Integration Test")
    print("=" * 60)
    print(f"테스트 시작 시간: {datetime.now().isoformat()}")
    print()
    
    # 환경 확인
    check_environment()
    
    # 테스트 실행
    tests = [
        ("환경 상태 테스트", test_browser_agent_without_api_key),
        ("취소 기능 테스트", test_cancel_functionality),
    ]
    
    # OpenAI API 키가 있으면 전체 테스트 실행
    if os.getenv("OPENAI_API_KEY"):
        tests.append(("브라우저 에이전트 실행 테스트", test_browser_agent_executor))
    else:
        print("⚠️ OPENAI_API_KEY가 설정되지 않아 일부 테스트를 건너뜁니다.")
        print()
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("=" * (len(test_name) + 3))
        
        try:
            await test_func()
            print(f"✅ {test_name} 완료")
        except Exception as e:
            print(f"❌ {test_name} 실패: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("🏁 모든 테스트 완료")
    print(f"테스트 종료 시간: {datetime.now().isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
