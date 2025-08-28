#!/usr/bin/env python3
"""
Integrated Browser Server 실행 스크립트
통합된 브라우저 서버를 간단하게 실행하기 위한 스크립트
"""

import asyncio
import os
import sys
import signal
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from integrated_browser_server import (
    IntegratedBrowserController,
    ProcessGPTBrowserAgentServer,
    app,
    BrowserUseAgentConfig
)


def setup_environment():
    """환경 설정"""
    # 필수 환경변수 설정
    if not os.getenv('DISPLAY'):
        os.environ['DISPLAY'] = ':99'
        
    # OpenAI API 키 확인
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("export OPENAI_API_KEY='your-api-key-here'")
        
    print(f"환경 설정:")
    print(f"  DISPLAY: {os.getenv('DISPLAY')}")
    print(f"  OPENAI_API_KEY: {'설정됨' if os.getenv('OPENAI_API_KEY') else '미설정'}")
    print(f"  작업 디렉토리: {os.getcwd()}")


def create_server_config():
    """서버 설정 생성"""
    config = BrowserUseAgentConfig(
        llm_model="gpt-4o-mini",
        headless=False,  # Docker 환경에서는 True로 설정
        save_recording_path="./recordings",
        max_actions=50,
        display=":99"
    )
    return config


async def run_server():
    """서버 실행"""
    print("🚀 Integrated Browser Server 시작 중...")
    
    # 환경 설정
    setup_environment()
    
    # 설정 생성
    config = create_server_config()
    
    # 컨트롤러 초기화
    controller = IntegratedBrowserController(config)
    
    # ProcessGPT 서버 초기화
    processgpt_server = ProcessGPTBrowserAgentServer(controller)
    
    try:
        # ProcessGPT 서버 시작
        await processgpt_server.start()
        print("✅ ProcessGPT Browser Agent Server 시작됨")
        
        # Flask 서버는 별도 스레드에서 실행
        print("🌐 Flask 서버 시작 (0.0.0.0:5001)")
        print("📋 사용 가능한 엔드포인트:")
        print("  - GET  /health              - 헬스 체크")
        print("  - GET  /status              - 상태 조회")
        print("  - POST /execute             - 자연어 태스크 실행")
        print("  - POST /processgpt/execute  - ProcessGPT 호환 실행")
        print("  - GET  /tasks/examples      - 태스크 예시 목록")
        print("  - GET  /test                - 테스트 엔드포인트")
        print()
        print("🛑 서버를 중지하려면 Ctrl+C를 누르세요")
        
        # Flask 앱 실행
        app.run(host='0.0.0.0', port=5001, debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 서버 종료 중...")
        await processgpt_server.stop()
        print("✅ 서버 종료 완료")
    except Exception as e:
        print(f"❌ 서버 실행 중 오류: {e}")
        await processgpt_server.stop()


def main():
    """메인 실행 함수"""
    print("🔧 Integrated Browser Server")
    print("=" * 50)
    
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
