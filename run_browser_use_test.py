#!/usr/bin/env python3
"""
Browser-Use Agent 테스트 실행 스크립트
간단한 실행을 위한 메인 스크립트
"""

import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from test_browser_use_agent import BrowserUseTestRunner


async def run_simple_test():
    """간단한 테스트 실행"""
    print("🌐 Browser-Use Agent 간단 테스트")
    print("=" * 40)
    
    runner = BrowserUseTestRunner()
    
    try:
        # 환경 설정
        await runner.setup()
        print("✅ 환경 설정 완료")
        
        # Google 검색 테스트만 실행
        print("\n🔍 Google 'playwright' 검색 테스트 실행...")
        result = await runner.test_google_search_playwright()
        
        if result and result.get('success'):
            print("✅ 테스트 성공!")
        else:
            print("❌ 테스트 실패")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        
    finally:
        # 리소스 정리
        if runner.model_client:
            await runner.model_client.close()


if __name__ == "__main__":
    # 환경변수 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경변수를 설정해주세요.")
        print("예: export OPENAI_API_KEY='your-api-key-here'")
        exit(1)
        
    # 테스트 실행
    asyncio.run(run_simple_test())
