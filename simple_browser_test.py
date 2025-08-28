#!/usr/bin/env python3
"""
간단한 Browser-Use 테스트
환경설정 및 기본 동작 확인용
"""

import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# browser-use 패키지 테스트
try:
    from browser_use import Agent
    print("✅ browser-use 패키지 import 성공")
    BROWSER_USE_AVAILABLE = True
except ImportError as e:
    print(f"❌ browser-use 패키지 import 실패: {e}")
    BROWSER_USE_AVAILABLE = False

# OpenAI API 키 확인
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    print(f"✅ OPENAI_API_KEY 설정됨 (길이: {len(openai_key)})")
else:
    print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")


async def test_simple_browser_use():
    """간단한 browser-use 테스트"""
    if not BROWSER_USE_AVAILABLE:
        print("browser-use를 사용할 수 없습니다.")
        return
        
    if not openai_key:
        print("OpenAI API 키가 필요합니다.")
        return
        
    try:
        print("\n🚀 Browser-Use Agent 테스트 시작")
        
        # 간단한 태스크로 Agent 생성
        agent = Agent(
            task="Google 홈페이지를 방문하세요",
            llm_model="gpt-4o-mini",
            headless=False,  # GUI 모드로 실행
            max_actions=5   # 최대 5개 액션으로 제한
        )
        
        print("Agent 생성 완료, 태스크 실행 시작...")
        
        # 태스크 실행
        result = await agent.run()
        
        print("✅ 태스크 실행 완료")
        print(f"결과: {result}")
        
        return result
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """메인 실행 함수"""
    print("🧪 Browser-Use 간단 테스트")
    print("=" * 40)
    
    # 환경 정보 출력
    print(f"Python 버전: {sys.version}")
    print(f"작업 디렉토리: {os.getcwd()}")
    print()
    
    # 테스트 실행
    await test_simple_browser_use()


if __name__ == "__main__":
    asyncio.run(main())
