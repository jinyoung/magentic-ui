#!/usr/bin/env python3
"""
Demo: Google에서 Playwright 검색하기
ProcessGPT AgentExecutor 형식의 Browser-Use Agent 데모
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from integrated_browser_server import (
    IntegratedBrowserController,
    BrowserUseAgentConfig,
    ProcessGPTBrowserAgentServer
)


async def demo_playwright_search():
    """Google에서 Playwright 검색 데모"""
    print("🎯 ProcessGPT Browser Agent Demo")
    print("=" * 50)
    print("태스크: Google에서 'playwright' 검색하기")
    print()
    
    # 환경변수 확인
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("데모를 실행하려면 OpenAI API 키가 필요합니다.")
        return
    
    print("✅ OpenAI API 키 확인됨")
    
    # 설정 생성
    config = BrowserUseAgentConfig(
        llm_model="gpt-4o-mini",
        headless=False,  # GUI 모드로 실행하여 동작 확인
        save_recording_path="./demo_recordings",
        max_actions=20,  # 데모이므로 액션 수 제한
        display=":0"     # 로컬 디스플레이 사용
    )
    
    print(f"🔧 브라우저 설정:")
    print(f"   모델: {config.llm_model}")
    print(f"   헤드리스: {config.headless}")
    print(f"   최대 액션: {config.max_actions}")
    print()
    
    # 컨트롤러 초기화
    print("🚀 브라우저 컨트롤러 초기화 중...")
    controller = IntegratedBrowserController(config)
    
    # ProcessGPT 서버 생성
    processgpt_server = ProcessGPTBrowserAgentServer(controller)
    
    try:
        # 서버 시작
        await processgpt_server.start()
        print("✅ ProcessGPT Browser Agent Server 시작됨")
        print()
        
        # 태스크 실행
        task = "Google에서 'playwright' 검색하기"
        print(f"🔍 태스크 실행: {task}")
        print("브라우저가 열리고 자동으로 검색을 수행합니다...")
        print()
        
        start_time = datetime.now()
        
        # AgentExecutor 패턴으로 실행
        result = await controller.execute_task(task)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 결과 출력
        print("=" * 50)
        print("🎉 실행 결과")
        print("=" * 50)
        print(f"태스크: {task}")
        print(f"실행 시간: {duration:.2f}초")
        print(f"성공 여부: {'✅ 성공' if result['success'] else '❌ 실패'}")
        print(f"타임스탬프: {result['timestamp']}")
        
        if result['success']:
            print("\n📋 상세 결과:")
            result_text = str(result['result'])
            # 결과를 보기 좋게 포맷팅
            if len(result_text) > 500:
                print(f"{result_text[:500]}...")
                print(f"\n(총 {len(result_text)}자 중 처음 500자만 표시)")
            else:
                print(result_text)
        else:
            print(f"\n❌ 오류: {result['error']}")
        
        # 상태 정보 출력
        status = processgpt_server.get_status()
        print(f"\n📊 에이전트 상태:")
        print(f"   총 실행 횟수: {status['execution_count']}")
        print(f"   브라우저 활성: {status['browser_active']}")
        print(f"   서버 실행 중: {status['server_running']}")
        
        print("\n🎯 데모 완료!")
        print("브라우저가 계속 열려있을 수 있습니다. 수동으로 닫아주세요.")
        
    except Exception as e:
        print(f"❌ 데모 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 리소스 정리
        await processgpt_server.stop()
        print("🧹 리소스 정리 완료")


async def simple_status_demo():
    """간단한 상태 확인 데모 (API 키 없이도 실행 가능)"""
    print("📊 간단한 상태 확인 데모")
    print("=" * 30)
    
    config = BrowserUseAgentConfig()
    controller = IntegratedBrowserController(config)
    server = ProcessGPTBrowserAgentServer(controller)
    
    await server.start()
    
    status = server.get_status()
    print("시스템 상태:")
    print(f"  Browser-Use 사용 가능: {status['browser_use_available']}")
    print(f"  ProcessGPT SDK 사용 가능: {status['processgpt_sdk_available']}")
    print(f"  에이전트 활성: {status['agent_active']}")
    print(f"  브라우저 활성: {status['browser_active']}")
    
    await server.stop()


def main():
    """메인 실행 함수"""
    print("🌟 Browser-Use ProcessGPT Agent Demo")
    print("=" * 50)
    print("이 데모는 다음을 보여줍니다:")
    print("1. ProcessGPT AgentExecutor 패턴 구현")
    print("2. Browser-Use를 통한 웹 자동화")
    print("3. 자연어 태스크 실행")
    print("4. 통합된 브라우저 세션 관리")
    print()
    
    # OpenAI API 키 확인
    if os.getenv('OPENAI_API_KEY'):
        print("🔑 OpenAI API 키 발견 - 전체 데모 실행")
        asyncio.run(demo_playwright_search())
    else:
        print("⚠️  OpenAI API 키 없음 - 상태 확인 데모만 실행")
        print("전체 데모를 실행하려면:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print()
        asyncio.run(simple_status_demo())


if __name__ == "__main__":
    main()
