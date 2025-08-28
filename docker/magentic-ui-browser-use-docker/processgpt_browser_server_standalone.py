#!/usr/bin/env python3
"""
ProcessGPT Browser Server - Standalone Version
ProcessGPT SDK 없이도 동작하는 독립실행형 브라우저 서버
"""

import asyncio
import os
import sys
import signal
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import json

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# python-dotenv로 환경변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available. Using system environment variables.")

# 로컬 모듈 imports
from browser_use_agent_executor import BrowserUseAgentExecutor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StandaloneBrowserServerManager:
    """독립실행형 브라우저 서버 관리자"""
    
    def __init__(self):
        self.executor: BrowserUseAgentExecutor = None
        self.is_running = False
        
        # 설정 로드
        self.config = self._load_config()
        
        # 신호 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self) -> Dict[str, Any]:
        """환경변수에서 설정 로드"""
        config = {
            # Browser-Use 설정
            "llm_model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
            "browser_headless": os.getenv("BROWSER_HEADLESS", "false").lower() == "true",
            "max_actions": int(os.getenv("MAX_ACTIONS", "50")),
            "task_timeout": int(os.getenv("TASK_TIMEOUT", "120")),
            "save_recordings": os.getenv("SAVE_RECORDINGS", "true").lower() == "true",
            
            # 서버 설정
            "polling_interval": int(os.getenv("POLLING_INTERVAL", "5")),
            "agent_orch": os.getenv("AGENT_ORCH", "browser_automation_agent"),
            
            # API 키
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "supabase_url": os.getenv("SUPABASE_URL"),
            "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY"),
        }
        
        return config
    
    def _signal_handler(self, signum, frame):
        """신호 핸들러 - 우아한 종료"""
        logger.info(f"신호 {signum} 수신 - 서버 종료 중...")
        self.is_running = False
    
    def _validate_config(self) -> tuple[bool, list[str]]:
        """설정 검증"""
        missing_vars = []
        warnings = []
        
        # 필수 환경변수 체크
        if not self.config["openai_api_key"]:
            missing_vars.append("OPENAI_API_KEY")
        
        # 선택적 환경변수 체크 (경고만)
        if not self.config["supabase_url"]:
            warnings.append("SUPABASE_URL이 설정되지 않음 - ProcessGPT 기능 제한")
        if not self.config["supabase_anon_key"]:
            warnings.append("SUPABASE_ANON_KEY가 설정되지 않음 - ProcessGPT 기능 제한")
        
        return len(missing_vars) == 0, missing_vars + warnings
    
    async def initialize(self):
        """서버 초기화"""
        logger.info("독립실행형 브라우저 서버 초기화 중...")
        
        # 설정 검증
        is_valid, messages = self._validate_config()
        
        if not is_valid:
            logger.error("설정 검증 실패:")
            for msg in messages:
                logger.error(f"  - {msg}")
            return False
        
        # 경고 메시지 출력
        for msg in messages:
            logger.warning(msg)
        
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
        
        return True
    
    async def simulate_processgpt_polling(self):
        """ProcessGPT 폴링 시뮬레이션 (실제 구현 시 Supabase 연동)"""
        polling_interval = self.config["polling_interval"]
        agent_orch = self.config["agent_orch"]
        
        logger.info(f"폴링 시뮬레이션 시작 - 간격: {polling_interval}초, 에이전트: {agent_orch}")
        
        demo_tasks = [
            "Google 홈페이지 방문하기",
            "네이버에서 '날씨' 검색하기",
            "GitHub 홈페이지로 이동하기",
            "현재 페이지의 제목 확인하기"
        ]
        
        task_index = 0
        
        while self.is_running:
            try:
                # 실제 구현에서는 Supabase에서 대기 중인 작업을 조회
                # 여기서는 데모용으로 순환하는 작업 실행
                if task_index < len(demo_tasks):
                    task = demo_tasks[task_index]
                    logger.info(f"데모 태스크 실행: {task}")
                    
                    # Mock context와 event queue
                    from test_processgpt_integration import MockRequestContext, MockEventQueue
                    
                    context = MockRequestContext(user_input=task)
                    event_queue = MockEventQueue()
                    
                    try:
                        await self.executor.execute(context, event_queue)
                        logger.info(f"태스크 완료: {task}")
                    except Exception as e:
                        logger.error(f"태스크 실행 실패: {e}")
                    
                    task_index += 1
                else:
                    # 모든 데모 태스크 완료 후 대기
                    logger.info("데모 태스크 모두 완료 - 대기 중...")
                
                # 폴링 간격만큼 대기
                await asyncio.sleep(polling_interval)
                
            except Exception as e:
                logger.error(f"폴링 루프 오류: {e}")
                await asyncio.sleep(polling_interval)
    
    async def start(self):
        """서버 시작"""
        if not await self.initialize():
            logger.error("서버 초기화 실패")
            return False
        
        self.is_running = True
        
        print("🚀 Standalone ProcessGPT Browser Server")
        print("=" * 60)
        print(f"📅 시작 시간: {datetime.now().isoformat()}")
        print(f"🤖 에이전트 타입: {self.config['agent_orch']}")
        print(f"⏱️  폴링 간격: {self.config['polling_interval']}초")
        print(f"🌐 브라우저 모드: {'헤드리스' if self.config['browser_headless'] else 'GUI'}")
        print(f"🧠 LLM 모델: {self.config['llm_model']}")
        print(f"🎯 최대 액션: {self.config['max_actions']}")
        print(f"⏰ 태스크 타임아웃: {self.config['task_timeout']}초")
        print()
        print("📋 설정된 환경변수:")
        print(f"  ✅ OPENAI_API_KEY: {'설정됨' if self.config['openai_api_key'] else '❌ 미설정'}")
        print(f"  ⚠️  SUPABASE_URL: {'설정됨' if self.config['supabase_url'] else '❌ 미설정'}")
        print(f"  ⚠️  SUPABASE_ANON_KEY: {'설정됨' if self.config['supabase_anon_key'] else '❌ 미설정'}")
        print()
        print("🔄 현재 모드: 독립실행형 (ProcessGPT SDK 없음)")
        print("📝 데모 태스크를 순환 실행합니다")
        print()
        print("🛑 서버를 중지하려면 Ctrl+C를 누르세요")
        print("=" * 60)
        
        try:
            # 폴링 시뮬레이션 시작
            await self.simulate_processgpt_polling()
            
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
        
        # 브라우저 리소스 정리
        if self.executor and hasattr(self.executor, 'browser_agent') and self.executor.browser_agent:
            try:
                logger.info("브라우저 리소스 정리 중...")
                # browser-use가 자동으로 정리하므로 별도 작업 불필요
            except Exception as e:
                logger.warning(f"브라우저 정리 중 오류: {e}")
        
        print("\n✅ 서버가 정상적으로 종료되었습니다")


async def main():
    """메인 실행 함수"""
    try:
        # 서버 관리자 생성 및 시작
        server_manager = StandaloneBrowserServerManager()
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
    
    if missing_packages:
        print(f"❌ 필수 패키지가 설치되지 않았습니다: {', '.join(missing_packages)}")
        print("다음 명령어로 설치하세요:")
        for pkg in missing_packages:
            print(f"  pip install {pkg}")
        sys.exit(1)
    
    # 메인 실행
    asyncio.run(main())
