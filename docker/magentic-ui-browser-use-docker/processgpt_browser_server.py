#!/usr/bin/env python3
"""
ProcessGPT Browser Server
ProcessGPT SDK를 사용한 브라우저 자동화 서버
"""

import asyncio
import os
import sys
import signal
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# ProcessGPT SDK imports
try:
    from processgpt_agent_sdk import ProcessGPTAgentServer
    PROCESSGPT_SDK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ProcessGPT SDK not available: {e}")
    print("pip install processgpt-agent-sdk 로 설치하세요.")
    PROCESSGPT_SDK_AVAILABLE = False

# 로컬 모듈 imports
from browser_use_agent_executor import BrowserUseAgentExecutor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProcessGPTBrowserServerConfig:
    """ProcessGPT 브라우저 서버 설정"""
    
    def __init__(self):
        # ProcessGPT 설정
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.polling_interval = int(os.getenv("POLLING_INTERVAL", "5"))
        self.agent_orch = os.getenv("AGENT_ORCH", "browser_automation_agent")
        
        # Browser-Use 설정
        self.llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.browser_headless = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
        self.max_actions = int(os.getenv("MAX_ACTIONS", "50"))
        self.task_timeout = int(os.getenv("TASK_TIMEOUT", "120"))
        self.save_recordings = os.getenv("SAVE_RECORDINGS", "true").lower() == "true"
        
        # 환경 검증
        self.validate()
    
    def validate(self):
        """설정 검증"""
        missing_vars = []
        
        if not self.supabase_url:
            missing_vars.append("SUPABASE_URL")
        if not self.supabase_anon_key:
            missing_vars.append("SUPABASE_ANON_KEY")
        if not os.getenv("OPENAI_API_KEY"):
            missing_vars.append("OPENAI_API_KEY")
            
        if missing_vars:
            raise ValueError(f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 반환"""
        return {
            "supabase_url": self.supabase_url,
            "polling_interval": self.polling_interval,
            "agent_orch": self.agent_orch,
            "llm_model": self.llm_model,
            "browser_headless": self.browser_headless,
            "max_actions": self.max_actions,
            "task_timeout": self.task_timeout,
            "save_recordings": self.save_recordings
        }


class ProcessGPTBrowserServerManager:
    """ProcessGPT 브라우저 서버 관리자"""
    
    def __init__(self, config: ProcessGPTBrowserServerConfig):
        self.config = config
        self.server: ProcessGPTAgentServer = None
        self.executor: BrowserUseAgentExecutor = None
        self.is_running = False
        
        # 신호 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """신호 핸들러 - 우아한 종료"""
        logger.info(f"신호 {signum} 수신 - 서버 종료 중...")
        if self.server:
            self.server.stop()
        self.is_running = False
    
    async def initialize(self):
        """서버 초기화"""
        logger.info("ProcessGPT 브라우저 서버 초기화 중...")
        
        # AgentExecutor 설정
        executor_config = {
            "llm_model": self.config.llm_model,
            "headless": self.config.browser_headless,
            "max_actions": self.config.max_actions,
            "timeout": self.config.task_timeout,
            "save_recording_path": "./recordings" if self.config.save_recordings else None
        }
        
        # AgentExecutor 생성
        self.executor = BrowserUseAgentExecutor(config=executor_config)
        logger.info(f"BrowserUseAgentExecutor 생성됨: {executor_config}")
        
        if not PROCESSGPT_SDK_AVAILABLE:
            logger.error("ProcessGPT SDK가 설치되지 않았습니다.")
            return False
        
        # ProcessGPT 서버 생성
        try:
            self.server = ProcessGPTAgentServer(
                executor=self.executor,
                polling_interval=self.config.polling_interval,
                agent_orch=self.config.agent_orch
            )
            logger.info(f"ProcessGPT 서버 생성됨 - 에이전트: {self.config.agent_orch}")
            return True
            
        except Exception as e:
            logger.error(f"ProcessGPT 서버 생성 실패: {e}")
            return False
    
    async def start(self):
        """서버 시작"""
        if not await self.initialize():
            logger.error("서버 초기화 실패")
            return False
        
        self.is_running = True
        
        print("🚀 ProcessGPT Browser Automation Server")
        print("=" * 60)
        print(f"📅 시작 시간: {datetime.now().isoformat()}")
        print(f"🤖 에이전트 타입: {self.config.agent_orch}")
        print(f"⏱️  폴링 간격: {self.config.polling_interval}초")
        print(f"🌐 브라우저 모드: {'헤드리스' if self.config.browser_headless else 'GUI'}")
        print(f"🧠 LLM 모델: {self.config.llm_model}")
        print(f"🎯 최대 액션: {self.config.max_actions}")
        print(f"⏰ 태스크 타임아웃: {self.config.task_timeout}초")
        print()
        print("📋 지원되는 작업:")
        print("  • 웹사이트 방문 및 탐색")
        print("  • 검색 및 정보 수집")
        print("  • 폼 작성 및 제출")
        print("  • 웹페이지 상호작용")
        print("  • 스크린샷 및 데이터 추출")
        print()
        print("🛑 서버를 중지하려면 Ctrl+C를 누르세요")
        print("=" * 60)
        
        try:
            # ProcessGPT 서버 실행 (무한 루프)
            await self.server.run()
            
        except KeyboardInterrupt:
            logger.info("사용자가 서버 중지를 요청했습니다")
        except Exception as e:
            logger.error(f"서버 실행 중 오류: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.stop()
    
    async def stop(self):
        """서버 중지"""
        logger.info("서버 종료 중...")
        self.is_running = False
        
        if self.server:
            try:
                self.server.stop()
                logger.info("ProcessGPT 서버 중지됨")
            except Exception as e:
                logger.warning(f"서버 중지 중 오류: {e}")
        
        # 추가 정리 작업
        if self.executor and hasattr(self.executor, 'browser_agent') and self.executor.browser_agent:
            try:
                # 브라우저 정리는 browser-use가 자동으로 처리
                logger.info("브라우저 리소스 정리 완료")
            except Exception as e:
                logger.warning(f"브라우저 정리 중 오류: {e}")
        
        print("\n✅ 서버가 정상적으로 종료되었습니다")


def print_usage():
    """사용법 출력"""
    print("ProcessGPT Browser Automation Server")
    print("=" * 50)
    print()
    print("필수 환경변수:")
    print("  SUPABASE_URL          - Supabase 프로젝트 URL")
    print("  SUPABASE_ANON_KEY     - Supabase 익명 키")
    print("  OPENAI_API_KEY        - OpenAI API 키")
    print()
    print("선택적 환경변수:")
    print("  POLLING_INTERVAL=5    - 폴링 간격 (초)")
    print("  AGENT_ORCH=browser_automation_agent - 에이전트 타입")
    print("  LLM_MODEL=gpt-4o-mini - 사용할 LLM 모델")
    print("  BROWSER_HEADLESS=false - 헤드리스 모드 여부")
    print("  MAX_ACTIONS=50        - 최대 액션 수")
    print("  TASK_TIMEOUT=120      - 태스크 타임아웃 (초)")
    print("  SAVE_RECORDINGS=true  - 브라우저 녹화 저장 여부")
    print()
    print("실행 예시:")
    print("  export SUPABASE_URL='https://your-project.supabase.co'")
    print("  export SUPABASE_ANON_KEY='your-anon-key'")
    print("  export OPENAI_API_KEY='your-api-key'")
    print("  python processgpt_browser_server.py")


async def main():
    """메인 실행 함수"""
    try:
        # 설정 로드 및 검증
        config = ProcessGPTBrowserServerConfig()
        
        # 서버 관리자 생성 및 시작
        server_manager = ProcessGPTBrowserServerManager(config)
        await server_manager.start()
        
    except ValueError as e:
        logger.error(f"설정 오류: {e}")
        print_usage()
        sys.exit(1)
    except Exception as e:
        logger.error(f"서버 시작 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Python 버전 체크
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 이상이 필요합니다")
        sys.exit(1)
    
    # 필수 패키지 체크
    missing_packages = []
    
    if not PROCESSGPT_SDK_AVAILABLE:
        missing_packages.append("processgpt-agent-sdk")
    
    try:
        import browser_use
    except ImportError:
        missing_packages.append("browser-use")
    
    if missing_packages:
        print(f"❌ 필수 패키지가 설치되지 않았습니다: {', '.join(missing_packages)}")
        print("다음 명령어로 설치하세요:")
        for pkg in missing_packages:
            print(f"  pip install {pkg}")
        sys.exit(1)
    
    # 메인 실행
    asyncio.run(main())
