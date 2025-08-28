#!/usr/bin/env python3
"""
ProcessGPT Browser Server with ProcessGPT Agent SDK
ProcessGPT Agent SDK를 사용하여 실제 ProcessGPT 작업을 처리하는 브라우저 서버
"""

import asyncio
import os
import sys
import signal
import logging
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# python-dotenv로 환경변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available. Using system environment variables.")

# ProcessGPT SDK imports
try:
    from processgpt_agent_sdk import ProcessGPTAgentServer
    from a2a.server.agent_execution import AgentExecutor, RequestContext
    from a2a.server.events import EventQueue, Event
    SDK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ProcessGPT SDK not available: {e}")
    print("Using fallback classes.")
    SDK_AVAILABLE = False

# 로컬 모듈 imports
from browser_use_agent_executor import BrowserUseAgentExecutor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Fallback classes for when ProcessGPT SDK is not available
if not SDK_AVAILABLE:
    class Event:
        def __init__(self, type: str, data: Dict):
            self.type = type
            self.data = data
    
    class EventQueue:
        def __init__(self):
            self.events = []
        
        def enqueue_event(self, event):
            self.events.append(event)
    
    class RequestContext:
        def __init__(self, user_input: str, context_data: Dict = None):
            self.user_input = user_input
            self.context_data = context_data or {}
        
        def get_user_input(self) -> str:
            return self.user_input
        
        def get_context_data(self) -> Dict:
            return self.context_data
    
    class AgentExecutor:
        async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
            pass


class ProcessGPTBrowserServerManager:
    """ProcessGPT SDK를 사용하는 브라우저 서버 관리자"""
    
    def __init__(self):
        self.executor: BrowserUseAgentExecutor = None
        self.server: Optional[ProcessGPTAgentServer] = None
        self.is_running = False
        
        # 설정 로드
        self.config = self._load_config()
        
        # 신호 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self) -> Dict[str, Any]:
        """환경변수에서 설정 로드"""
        config = {
            # Supabase 설정
            "supabase_url": os.getenv("SUPABASE_URL"),
            "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY"),
            
            # Browser-Use 설정
            "llm_model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
            "browser_headless": os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
            "max_actions": int(os.getenv("MAX_ACTIONS", "30")),
            "task_timeout": int(os.getenv("TASK_TIMEOUT", "120")),
            "save_recordings": os.getenv("SAVE_RECORDINGS", "true").lower() == "true",
            
            # ProcessGPT 서버 설정
            "polling_interval": int(os.getenv("POLLING_INTERVAL", "5")),
            "agent_orch": os.getenv("AGENT_ORCH", "browser_automation_agent"),
            
            # API 키
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
        }
        
        return config
    
    def _signal_handler(self, signum, frame):
        """신호 핸들러 - 우아한 종료"""
        logger.info(f"신호 {signum} 수신 - 서버 종료 중...")
        self.is_running = False
    
    def _validate_config(self) -> tuple[bool, list[str]]:
        """설정 검증"""
        missing_vars = []
        
        # 필수 환경변수 체크
        if not self.config["openai_api_key"]:
            missing_vars.append("OPENAI_API_KEY")
        if not self.config["supabase_url"]:
            missing_vars.append("SUPABASE_URL")
        if not self.config["supabase_anon_key"]:
            missing_vars.append("SUPABASE_ANON_KEY")
        
        return len(missing_vars) == 0, missing_vars
    
    async def initialize(self):
        """서버 초기화"""
        logger.info("ProcessGPT SDK 브라우저 서버 초기화 중...")
        
        # 설정 검증
        is_valid, missing_vars = self._validate_config()
        
        if not is_valid:
            logger.error("설정 검증 실패:")
            for var in missing_vars:
                logger.error(f"  - {var}")
            return False
        
        # AgentExecutor 설정
        executor_config = {
            "llm_model": self.config["llm_model"],
            "headless": self.config["browser_headless"],
            "max_actions": self.config["max_actions"],
            "timeout": self.config["task_timeout"],
            "save_recording_path": "./recordings" if self.config["save_recordings"] else None
        }
        
        # AgentExecutor 생성
        self.executor = BrowserUseAgentExecutor(config=executor_config)
        logger.info(f"BrowserUseAgentExecutor 생성됨: {executor_config}")
        
        # ProcessGPT 서버 생성 (SDK 사용 가능한 경우만)
        if SDK_AVAILABLE:
            self.server = ProcessGPTAgentServer(
                executor=self.executor,
                polling_interval=self.config["polling_interval"],
                agent_orch=self.config["agent_orch"]
            )
            logger.info("✅ ProcessGPT 서버 생성 완료")
        else:
            logger.warning("⚠️ ProcessGPT SDK를 사용할 수 없어 폴백 모드로 실행됩니다")
        
        return True
    

    
    async def start(self):
        """서버 시작"""
        if not await self.initialize():
            logger.error("서버 초기화 실패")
            return False
        
        print("🚀 ProcessGPT Browser Server with Supabase")
        print("=" * 60)
        print(f"📅 시작 시간: {datetime.now().isoformat()}")
        print(f"🤖 에이전트 타입: {self.config['agent_orch']}")
        print(f"⏱️  폴링 간격: {self.config['polling_interval']}초")
        print(f"🌐 브라우저 모드: {'헤드리스' if self.config['browser_headless'] else 'GUI'}")
        print(f"🧠 LLM 모델: {self.config['llm_model']}")
        print(f"🎯 최대 액션: {self.config['max_actions']}")
        print(f"⏰ 태스크 타임아웃: {self.config['task_timeout']}초")
        print()
        print(f"🗄️  Supabase URL: {self.config['supabase_url']}")
        print(f"🔑 API 키 설정: {'✅' if self.config['openai_api_key'] else '❌'}")
        print()
        print("🔄 ProcessGPT SDK로 Supabase todolist 테이블을 폴링하여 작업을 처리합니다")
        print("🛑 서버를 중지하려면 Ctrl+C를 누르세요")
        print("=" * 60)
        
        try:
            # ProcessGPT 서버 시작 (SDK 사용 가능한 경우)
            if SDK_AVAILABLE and self.server:
                logger.info("ProcessGPT SDK 서버 시작...")
                await self.server.start()
            else:
                # 폴백 모드 - 기본 폴링 유지
                logger.warning("SDK가 없어 폴백 모드로 실행됩니다")
                await self._fallback_polling_loop()
                
        except KeyboardInterrupt:
            logger.info("사용자가 서버 중지를 요청했습니다")
        except Exception as e:
            logger.error(f"서버 실행 중 오류: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.stop()
    
    async def _fallback_polling_loop(self):
        """SDK 없이 사용할 폴백 폴링 루프"""
        polling_interval = self.config["polling_interval"]
        agent_orch = self.config["agent_orch"]
        
        logger.info(f"폴백 폴링 시작 - 간격: {polling_interval}초, 에이전트: {agent_orch}")
        
        self.is_running = True
        while self.is_running:
            try:
                logger.debug("폴백 모드에서 실행 중...")
                await asyncio.sleep(polling_interval)
                
            except Exception as e:
                logger.error(f"폴백 폴링 루프 오류: {e}")
                await asyncio.sleep(polling_interval)
    
    async def stop(self):
        """서버 중지"""
        logger.info("서버 종료 중...")
        self.is_running = False
        
        # ProcessGPT 서버 중지 (SDK 사용 중인 경우)
        if SDK_AVAILABLE and self.server:
            try:
                logger.info("ProcessGPT 서버 중지 중...")
                await self.server.stop()
            except Exception as e:
                logger.warning(f"ProcessGPT 서버 중지 중 오류: {e}")
        
        # 브라우저 리소스 정리
        if self.executor and hasattr(self.executor, 'browser_agent') and self.executor.browser_agent:
            try:
                logger.info("브라우저 리소스 정리 중...")
            except Exception as e:
                logger.warning(f"브라우저 정리 중 오류: {e}")
        
        print("\n✅ 서버가 정상적으로 종료되었습니다")


async def main():
    """메인 실행 함수"""
    try:
        # 서버 관리자 생성 및 시작
        server_manager = ProcessGPTBrowserServerManager()
        await server_manager.start()
        
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
    
    try:
        import browser_use
    except ImportError:
        missing_packages.append("browser-use")
    
    try:
        import aiohttp
    except ImportError:
        missing_packages.append("aiohttp")
    
    if missing_packages:
        print(f"❌ 필수 패키지가 설치되지 않았습니다: {', '.join(missing_packages)}")
        print("다음 명령어로 설치하세요:")
        for pkg in missing_packages:
            print(f"  pip install {pkg}")
        sys.exit(1)
    
    # 메인 실행
    asyncio.run(main())
