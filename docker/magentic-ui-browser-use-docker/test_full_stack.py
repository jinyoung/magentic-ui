#!/usr/bin/env python3
"""
Full Stack Test Script
Docker Compose로 실행된 전체 스택 테스트
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, List


class FullStackTester:
    """전체 스택 테스트 클래스"""
    
    def __init__(self):
        # 서비스 URL 설정
        self.supabase_url = "http://localhost:54321"
        self.browser_api_url = "http://localhost:5001"
        self.supabase_studio_url = "http://localhost:3001"
        
        # Supabase API 키 (테스트용 고정값)
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
        
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }
    
    async def wait_for_services(self, max_attempts: int = 30):
        """서비스들이 시작될 때까지 대기"""
        print("🔄 서비스 시작 대기 중...")
        
        services = {
            "Supabase API": f"{self.supabase_url}/rest/v1/",
            "Browser API": f"{self.browser_api_url}/health",
            "Supabase Studio": f"{self.supabase_studio_url}/"
        }
        
        for service_name, url in services.items():
            print(f"   ⏳ {service_name} 대기 중...")
            
            for attempt in range(max_attempts):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=5) as response:
                            if response.status in [200, 404]:  # 404도 서비스가 응답하는 것으로 간주
                                print(f"   ✅ {service_name} 준비됨")
                                break
                except:
                    if attempt == max_attempts - 1:
                        print(f"   ❌ {service_name} 시작 실패")
                        return False
                    await asyncio.sleep(2)
        
        print("✅ 모든 서비스 준비 완료")
        return True
    
    async def test_supabase_connection(self) -> bool:
        """Supabase 연결 테스트"""
        print("\n🗄️  Supabase 연결 테스트")
        print("-" * 30)
        
        try:
            # Health check
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.supabase_url}/rest/v1/rpc/health_check",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"✅ Supabase 헬스체크 성공")
                        print(f"   상태: {health_data.get('status')}")
                        print(f"   대기 작업 수: {health_data.get('pending_tasks')}")
                        return True
                    else:
                        print(f"❌ Supabase 헬스체크 실패: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Supabase 연결 오류: {e}")
            return False
    
    async def test_todolist_operations(self) -> bool:
        """todolist 테이블 CRUD 테스트"""
        print("\n📝 TodoList 테이블 테스트")
        print("-" * 30)
        
        try:
            async with aiohttp.ClientSession() as session:
                # 1. 기존 작업 조회
                async with session.get(
                    f"{self.supabase_url}/rest/v1/todolist?select=*&limit=5",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        tasks = await response.json()
                        print(f"✅ 기존 작업 조회 성공: {len(tasks)}개")
                    else:
                        print(f"❌ 작업 조회 실패: {response.status}")
                        return False
                
                # 2. 새 작업 추가
                new_task = {
                    "activity_name": "test_full_stack_task",
                    "description": "Docker Compose 풀스택 테스트 작업",
                    "status": "PENDING",
                    "agent_orch": "browser_automation_agent",
                    "user_id": "test-fullstack-user"
                }
                
                async with session.post(
                    f"{self.supabase_url}/rest/v1/todolist",
                    headers=self.headers,
                    json=new_task
                ) as response:
                    if response.status in [200, 201]:
                        print("✅ 새 작업 추가 성공")
                        return True
                    else:
                        print(f"❌ 작업 추가 실패: {response.status}")
                        error_text = await response.text()
                        print(f"   오류 내용: {error_text}")
                        return False
                        
        except Exception as e:
            print(f"❌ TodoList 테스트 오류: {e}")
            return False
    
    async def test_browser_api(self) -> bool:
        """Browser API 테스트"""
        print("\n🌐 Browser API 테스트")
        print("-" * 30)
        
        try:
            async with aiohttp.ClientSession() as session:
                # Health check
                async with session.get(f"{self.browser_api_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print("✅ Browser API 헬스체크 성공")
                        print(f"   상태: {health_data.get('status')}")
                        print(f"   browser-use 사용 가능: {health_data.get('browser_use_available')}")
                        return True
                    else:
                        print(f"❌ Browser API 헬스체크 실패: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Browser API 테스트 오류: {e}")
            return False
    
    async def test_end_to_end_workflow(self) -> bool:
        """전체 워크플로우 테스트"""
        print("\n🔄 End-to-End 워크플로우 테스트")
        print("-" * 40)
        
        try:
            async with aiohttp.ClientSession() as session:
                # 1. 특별한 테스트 작업 추가
                test_task = {
                    "activity_name": "e2e_test_task",
                    "description": "Google 홈페이지 방문하기 (E2E 테스트)",
                    "status": "PENDING",
                    "agent_orch": "browser_automation_agent",
                    "user_id": "e2e-test-user"
                }
                
                print("1. 테스트 작업 추가 중...")
                async with session.post(
                    f"{self.supabase_url}/rest/v1/todolist",
                    headers=self.headers,
                    json=test_task
                ) as response:
                    if response.status not in [200, 201]:
                        print(f"❌ 작업 추가 실패: {response.status}")
                        return False
                
                print("✅ 테스트 작업 추가됨")
                
                # 2. 작업이 처리될 때까지 대기 (최대 2분)
                print("2. 작업 처리 대기 중...")
                max_wait_time = 120  # 2분
                check_interval = 10  # 10초마다 확인
                
                for i in range(0, max_wait_time, check_interval):
                    await asyncio.sleep(check_interval)
                    
                    # 작업 상태 확인
                    async with session.get(
                        f"{self.supabase_url}/rest/v1/todolist?activity_name=eq.e2e_test_task&order=created_at.desc&limit=1",
                        headers=self.headers
                    ) as response:
                        if response.status == 200:
                            tasks = await response.json()
                            if tasks:
                                task = tasks[0]
                                status = task['status']
                                print(f"   작업 상태: {status} ({i+check_interval}초 경과)")
                                
                                if status in ['DONE', 'CANCELLED']:
                                    if status == 'DONE':
                                        print("✅ 작업이 성공적으로 완료되었습니다!")
                                        output = task.get('output', {})
                                        if output:
                                            print(f"   결과: {output.get('message', 'N/A')}")
                                        return True
                                    else:
                                        print("❌ 작업이 취소되었습니다")
                                        return False
                
                print("⏰ 작업 처리 타임아웃")
                return False
                
        except Exception as e:
            print(f"❌ E2E 테스트 오류: {e}")
            return False
    
    async def test_events_logging(self) -> bool:
        """이벤트 로깅 테스트"""
        print("\n📊 이벤트 로깅 테스트")
        print("-" * 30)
        
        try:
            async with aiohttp.ClientSession() as session:
                # 최근 이벤트 조회
                async with session.get(
                    f"{self.supabase_url}/rest/v1/events?order=created_at.desc&limit=10",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        events = await response.json()
                        print(f"✅ 최근 이벤트 조회 성공: {len(events)}개")
                        
                        # 최근 이벤트 출력
                        for i, event in enumerate(events[:3]):
                            print(f"   {i+1}. {event['event_type']}: {event.get('message', 'N/A')}")
                        
                        return True
                    else:
                        print(f"❌ 이벤트 조회 실패: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ 이벤트 로깅 테스트 오류: {e}")
            return False
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🧪 ProcessGPT Browser Automation Full Stack Test")
        print("=" * 60)
        print(f"테스트 시작 시간: {datetime.now().isoformat()}")
        print()
        
        # 서비스 대기
        if not await self.wait_for_services():
            print("❌ 서비스 시작 실패")
            return
        
        # 테스트 목록
        tests = [
            ("Supabase 연결", self.test_supabase_connection),
            ("TodoList 테이블", self.test_todolist_operations),
            ("Browser API", self.test_browser_api),
            ("이벤트 로깅", self.test_events_logging),
            ("End-to-End 워크플로우", self.test_end_to_end_workflow),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n🧪 {test_name} 테스트")
            print("=" * (len(test_name) + 6))
            
            start_time = time.time()
            try:
                success = await test_func()
                end_time = time.time()
                
                results[test_name] = {
                    "success": success,
                    "duration": end_time - start_time
                }
                
                status = "✅ 성공" if success else "❌ 실패"
                print(f"\n{status} (소요시간: {end_time - start_time:.2f}초)")
                
            except Exception as e:
                end_time = time.time()
                results[test_name] = {
                    "success": False,
                    "duration": end_time - start_time,
                    "error": str(e)
                }
                print(f"\n❌ 실패: {e}")
        
        # 최종 결과 요약
        print(f"\n{'='*60}")
        print("🏁 테스트 결과 요약")
        print(f"{'='*60}")
        
        successful_tests = sum(1 for r in results.values() if r['success'])
        total_tests = len(results)
        
        print(f"전체 테스트: {total_tests}")
        print(f"성공한 테스트: {successful_tests}")
        print(f"실패한 테스트: {total_tests - successful_tests}")
        print(f"성공률: {(successful_tests/total_tests)*100:.1f}%")
        print()
        
        for test_name, result in results.items():
            status = "✅ 성공" if result['success'] else "❌ 실패"
            duration = result['duration']
            print(f"{test_name:25} | {status} | {duration:6.2f}초")
        
        print(f"\n테스트 완료 시간: {datetime.now().isoformat()}")
        
        # 접속 정보 출력
        print(f"\n💡 서비스 접속 정보:")
        print(f"  📊 Supabase Studio: http://localhost:3001")
        print(f"  🌐 Browser noVNC: http://localhost:6080")
        print(f"  🔧 Browser API: http://localhost:5001")
        print(f"  🗄️  Supabase API: http://localhost:54321")
        
        return results


async def main():
    """메인 실행 함수"""
    tester = FullStackTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
