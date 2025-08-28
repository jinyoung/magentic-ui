#!/usr/bin/env python3
"""
Integrated Browser Server 테스트 스크립트
통합된 브라우저 서버와 ProcessGPT Agent 테스트
"""

import asyncio
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any


class IntegratedServerTester:
    """통합 서버 테스트 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        
    def test_health_check(self) -> Dict[str, Any]:
        """헬스 체크 테스트"""
        print("🏥 헬스 체크 테스트...")
        try:
            response = requests.get(f"{self.base_url}/health")
            result = response.json()
            print(f"   상태: {response.status_code}")
            print(f"   응답: {result}")
            return result
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            return {"error": str(e)}
    
    def test_status(self) -> Dict[str, Any]:
        """상태 조회 테스트"""
        print("📊 상태 조회 테스트...")
        try:
            response = requests.get(f"{self.base_url}/status")
            result = response.json()
            print(f"   상태: {response.status_code}")
            print(f"   browser-use 사용 가능: {result.get('browser_use_available')}")
            print(f"   ProcessGPT SDK 사용 가능: {result.get('processgpt_sdk_available')}")
            print(f"   실행 횟수: {result.get('execution_count')}")
            return result
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            return {"error": str(e)}
    
    def test_task_examples(self) -> Dict[str, Any]:
        """태스크 예시 테스트"""
        print("📋 태스크 예시 조회 테스트...")
        try:
            response = requests.get(f"{self.base_url}/tasks/examples")
            result = response.json()
            print(f"   상태: {response.status_code}")
            if result.get('success'):
                examples = result.get('examples', [])
                print(f"   예시 개수: {len(examples)}")
                for i, example in enumerate(examples[:2]):  # 처음 2개만 출력
                    print(f"   {i+1}. {example['title']}: {example['task']}")
            return result
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            return {"error": str(e)}
    
    def test_simple_execution(self) -> Dict[str, Any]:
        """간단한 태스크 실행 테스트"""
        print("🚀 간단한 태스크 실행 테스트...")
        task = "Google 홈페이지 방문하기"
        
        try:
            payload = {"task": task}
            response = requests.post(
                f"{self.base_url}/execute",
                json=payload,
                timeout=60  # 60초 타임아웃
            )
            result = response.json()
            print(f"   상태: {response.status_code}")
            print(f"   태스크: {task}")
            print(f"   성공 여부: {result.get('success')}")
            if result.get('success'):
                print(f"   실행 시간: {result.get('timestamp')}")
                print(f"   결과 (첫 200자): {str(result.get('result', ''))[:200]}...")
            else:
                print(f"   오류: {result.get('error')}")
            return result
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            return {"error": str(e)}
    
    def test_google_playwright_search(self) -> Dict[str, Any]:
        """Google에서 Playwright 검색 테스트"""
        print("🔍 Google Playwright 검색 테스트...")
        task = "Google에서 'playwright' 검색하기"
        
        try:
            payload = {"task": task}
            response = requests.post(
                f"{self.base_url}/execute",
                json=payload,
                timeout=120  # 2분 타임아웃
            )
            result = response.json()
            print(f"   상태: {response.status_code}")
            print(f"   태스크: {task}")
            print(f"   성공 여부: {result.get('success')}")
            if result.get('success'):
                print(f"   실행 시간: {result.get('timestamp')}")
                print(f"   실행 횟수: {result.get('execution_count')}")
                result_text = str(result.get('result', ''))
                print(f"   결과 (첫 300자): {result_text[:300]}...")
            else:
                print(f"   오류: {result.get('error')}")
                if 'traceback' in result:
                    print(f"   스택 트레이스: {result['traceback'][:500]}...")
            return result
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            return {"error": str(e)}
    
    def test_processgpt_execute(self) -> Dict[str, Any]:
        """ProcessGPT 호환 실행 엔드포인트 테스트"""
        print("🤖 ProcessGPT 호환 실행 테스트...")
        task = "GitHub 홈페이지로 이동하기"
        
        try:
            payload = {
                "task": task,
                "parameters": {
                    "timeout": 60
                }
            }
            response = requests.post(
                f"{self.base_url}/processgpt/execute",
                json=payload,
                timeout=90
            )
            result = response.json()
            print(f"   상태: {response.status_code}")
            print(f"   태스크: {task}")
            print(f"   성공 여부: {result.get('success')}")
            if result.get('success'):
                print(f"   실행 시간: {result.get('timestamp')}")
                result_text = str(result.get('result', ''))
                print(f"   결과 (첫 200자): {result_text[:200]}...")
            else:
                print(f"   오류: {result.get('error')}")
            return result
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            return {"error": str(e)}
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🧪 Integrated Browser Server 전체 테스트 시작")
        print("=" * 60)
        print(f"서버 URL: {self.base_url}")
        print(f"테스트 시작 시간: {datetime.now().isoformat()}")
        print()
        
        # 순차적으로 테스트 실행
        tests = [
            ("헬스 체크", self.test_health_check),
            ("상태 조회", self.test_status),
            ("태스크 예시", self.test_task_examples),
            ("간단한 실행", self.test_simple_execution),
            ("Google Playwright 검색", self.test_google_playwright_search),
            ("ProcessGPT 호환 실행", self.test_processgpt_execute),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            start_time = time.time()
            result = test_func()
            end_time = time.time()
            
            results[test_name] = {
                "result": result,
                "duration": end_time - start_time,
                "success": not ("error" in result and result["error"])
            }
            
            print(f"   실행 시간: {end_time - start_time:.2f}초")
            print(f"   성공: {'✅' if results[test_name]['success'] else '❌'}")
            
            # 테스트 간 잠시 대기
            time.sleep(2)
        
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
        
        for test_name, result_info in results.items():
            status = "✅ 성공" if result_info['success'] else "❌ 실패"
            duration = result_info['duration']
            print(f"{test_name:20} | {status} | {duration:6.2f}초")
        
        print(f"\n테스트 완료 시간: {datetime.now().isoformat()}")
        
        return results


def main():
    """메인 실행 함수"""
    print("🔧 Integrated Browser Server 테스트 도구")
    print("=" * 50)
    print("이 도구는 통합된 브라우저 서버를 테스트합니다.")
    print("서버가 http://localhost:5001에서 실행 중이어야 합니다.")
    print()
    
    # 서버 연결 확인
    tester = IntegratedServerTester()
    
    try:
        # 간단한 연결 테스트
        response = requests.get(f"{tester.base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 서버 연결 확인됨")
        else:
            print(f"⚠️ 서버 응답 상태: {response.status_code}")
    except Exception as e:
        print(f"❌ 서버에 연결할 수 없습니다: {e}")
        print("다음을 확인하세요:")
        print("1. 서버가 실행 중인지 확인")
        print("2. Docker 컨테이너가 시작되었는지 확인")
        print("3. 포트 5001이 열려있는지 확인")
        return
    
    print()
    
    # 전체 테스트 실행
    results = tester.run_all_tests()
    
    # 추가 정보 출력
    print(f"\n💡 추가 정보:")
    print(f"- 서버 로그를 확인하려면 Docker 컨테이너 로그를 확인하세요")
    print(f"- API 문서: {tester.base_url}/test")
    print(f"- 헬스 체크: {tester.base_url}/health")
    print(f"- 상태 조회: {tester.base_url}/status")


if __name__ == "__main__":
    main()
