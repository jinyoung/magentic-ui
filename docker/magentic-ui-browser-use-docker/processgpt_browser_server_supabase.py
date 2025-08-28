#!/usr/bin/env python3
"""
ProcessGPT Browser Server with Supabase Integration
Supabase를 사용하여 실제 ProcessGPT 작업을 처리하는 브라우저 서버
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
import aiohttp

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


class SupabaseClient:
    """Supabase 클라이언트"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.base_url = supabase_url.rstrip('/')
        self.headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
    async def get_next_task(self, agent_type: str = 'browser_automation_agent') -> Optional[Dict[str, Any]]:
        """다음 대기 중인 작업 가져오기"""
        try:
            url = f"{self.base_url}/rest/v1/rpc/get_next_task"
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json={"agent_type": agent_type}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data[0] if data else None
                    else:
                        logger.error(f"Failed to get next task: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting next task: {e}")
            return None
    
    async def update_task_status(self, task_id: str, status: str, output: Optional[Dict] = None) -> bool:
        """작업 상태 업데이트"""
        try:
            url = f"{self.base_url}/rest/v1/rpc/update_task_status"
            payload = {
                "task_id": task_id,
                "new_status": status
            }
            if output:
                payload["result_output"] = output
                
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=payload
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return False
    
    async def log_event(self, task_id: str, event_type: str, event_data: Dict, message: str = "") -> bool:
        """이벤트 로깅"""
        try:
            url = f"{self.base_url}/rest/v1/events"
            payload = {
                "todolist_id": task_id,
                "event_type": event_type,
                "event_data": event_data,
                "message": message
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=payload
                ) as response:
                    return response.status in [200, 201]
        except Exception as e:
            logger.error(f"Error logging event: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Supabase 연결 상태 확인"""
        try:
            url = f"{self.base_url}/rest/v1/rpc/health_check"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"status": "error", "code": response.status}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class MockEventQueue:
    """Supabase 로깅을 위한 EventQueue 구현"""
    
    def __init__(self, supabase_client: SupabaseClient, task_id: str):
        self.supabase = supabase_client
        self.task_id = task_id
        self.events = []
    
    def enqueue_event(self, event):
        """이벤트를 Supabase에 로깅"""
        self.events.append(event)
        # 비동기 로깅 (fire and forget)
        asyncio.create_task(self._log_to_supabase(event))
    
    async def _log_to_supabase(self, event):
        """Supabase에 이벤트 로깅"""
        try:
            await self.supabase.log_event(
                task_id=self.task_id,
                event_type=event.type,
                event_data=event.data,
                message=event.data.get('message', '')
            )
        except Exception as e:
            logger.warning(f"Failed to log event to Supabase: {e}")


class MockRequestContext:
    """ProcessGPT SDK RequestContext 모의 구현"""
    
    def __init__(self, user_input: str, context_data: Dict = None):
        self.user_input = user_input
        self.context_data = context_data or {}
    
    def get_user_input(self) -> str:
        return self.user_input
    
    def get_context_data(self) -> Dict:
        return self.context_data


class MockEvent:
    """ProcessGPT SDK Event 모의 구현"""
    
    def __init__(self, type: str, data: Dict):
        self.type = type
        self.data = data


class SupabaseBrowserServerManager:
    """Supabase 연동 브라우저 서버 관리자"""
    
    def __init__(self):
        self.executor: BrowserUseAgentExecutor = None
        self.supabase: SupabaseClient = None
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
            
            # 서버 설정
            "polling_interval": int(os.getenv("POLLING_INTERVAL", "10")),
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
        logger.info("Supabase 연동 브라우저 서버 초기화 중...")
        
        # 설정 검증
        is_valid, missing_vars = self._validate_config()
        
        if not is_valid:
            logger.error("설정 검증 실패:")
            for var in missing_vars:
                logger.error(f"  - {var}")
            return False
        
        # Supabase 클라이언트 초기화
        self.supabase = SupabaseClient(
            self.config["supabase_url"],
            self.config["supabase_anon_key"]
        )
        
        # Supabase 연결 테스트
        health = await self.supabase.health_check()
        if health.get("status") != "healthy":
            logger.error(f"Supabase 연결 실패: {health}")
            return False
        
        logger.info("✅ Supabase 연결 성공")
        
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
    
    async def process_task(self, task: Dict[str, Any]) -> bool:
        """단일 작업 처리"""
        task_id = task["task_id"]
        description = task["description"]
        
        logger.info(f"작업 처리 시작: {task_id} - {description}")
        
        # 작업 상태를 IN_PROGRESS로 업데이트
        await self.supabase.update_task_status(task_id, "IN_PROGRESS")
        
        try:
            # Mock context 및 event queue 생성
            context = MockRequestContext(user_input=description)
            event_queue = MockEventQueue(self.supabase, task_id)
            
            # AgentExecutor 실행
            await self.executor.execute(context, event_queue)
            
            # 성공 상태로 업데이트
            result_output = {
                "success": True,
                "message": "작업이 성공적으로 완료되었습니다",
                "task_id": task_id,
                "completed_at": datetime.now().isoformat(),
                "events_count": len(event_queue.events)
            }
            
            await self.supabase.update_task_status(task_id, "DONE", result_output)
            logger.info(f"✅ 작업 완료: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 작업 실행 실패: {task_id} - {e}")
            
            # 실패 상태로 업데이트
            error_output = {
                "success": False,
                "error": str(e),
                "task_id": task_id,
                "failed_at": datetime.now().isoformat(),
                "traceback": traceback.format_exc()
            }
            
            await self.supabase.update_task_status(task_id, "CANCELLED", error_output)
            return False
    
    async def polling_loop(self):
        """Supabase 폴링 루프"""
        polling_interval = self.config["polling_interval"]
        agent_orch = self.config["agent_orch"]
        
        logger.info(f"폴링 시작 - 간격: {polling_interval}초, 에이전트: {agent_orch}")
        
        while self.is_running:
            try:
                # 다음 대기 작업 가져오기
                task = await self.supabase.get_next_task(agent_orch)
                
                if task:
                    # 작업 처리
                    await self.process_task(task)
                else:
                    # 대기 중인 작업이 없음
                    logger.debug("대기 중인 작업이 없습니다")
                
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
        print("🔄 Supabase todolist 테이블을 폴링하여 작업을 처리합니다")
        print("🛑 서버를 중지하려면 Ctrl+C를 누르세요")
        print("=" * 60)
        
        try:
            # 폴링 루프 시작
            await self.polling_loop()
            
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
            except Exception as e:
                logger.warning(f"브라우저 정리 중 오류: {e}")
        
        print("\n✅ 서버가 정상적으로 종료되었습니다")


async def main():
    """메인 실행 함수"""
    try:
        # 서버 관리자 생성 및 시작
        server_manager = SupabaseBrowserServerManager()
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
