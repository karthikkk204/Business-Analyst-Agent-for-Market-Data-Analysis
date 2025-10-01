"""Basic API tests for CrewInsight MVP."""

import asyncio
import httpx
import json
import time
from typing import Dict, Any


class CrewInsightTester:
    """Test client for CrewInsight API."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "crewinsight-mvp-2024"):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def test_health_check(self) -> bool:
        """Test health check endpoint."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print("✅ Health check passed")
                print(f"   Status: {data.get('status')}")
                print(f"   Services: {data.get('services', {})}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_root_endpoint(self) -> bool:
        """Test root endpoint."""
        try:
            response = await self.client.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                print("✅ Root endpoint working")
                print(f"   Message: {data.get('message')}")
                return True
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
            return False
    
    async def test_analyze_endpoint(self) -> str:
        """Test analysis endpoint and return analysis ID."""
        try:
            payload = {
                "market": "technology",
                "region": "US",
                "timeframe": "1w",
                "api_key": self.api_key
            }
            
            response = await self.client.post(
                f"{self.base_url}/analyze",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                analysis_id = data.get("analysis_id")
                print("✅ Analysis started successfully")
                print(f"   Analysis ID: {analysis_id}")
                print(f"   Status: {data.get('status')}")
                return analysis_id
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return None
    
    async def test_results_endpoint(self, analysis_id: str) -> bool:
        """Test results endpoint."""
        try:
            response = await self.client.get(
                f"{self.base_url}/results/{analysis_id}",
                params={"api_key": self.api_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Results retrieved successfully")
                print(f"   Status: {data.get('status')}")
                print(f"   Trends found: {len(data.get('trends', []))}")
                print(f"   Summary length: {len(data.get('summary', ''))}")
                return True
            else:
                print(f"❌ Results failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Results error: {e}")
            return False
    
    async def test_invalid_api_key(self) -> bool:
        """Test with invalid API key."""
        try:
            payload = {
                "market": "technology",
                "region": "US",
                "timeframe": "1w",
                "api_key": "invalid-key"
            }
            
            response = await self.client.post(
                f"{self.base_url}/analyze",
                json=payload
            )
            
            if response.status_code == 401:
                print("✅ Invalid API key properly rejected")
                return True
            else:
                print(f"❌ Invalid API key not rejected: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Invalid API key test error: {e}")
            return False
    
    async def test_list_analyses(self) -> bool:
        """Test list analyses endpoint."""
        try:
            response = await self.client.get(
                f"{self.base_url}/results",
                params={"api_key": self.api_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ List analyses working")
                print(f"   Found {len(data)} analyses")
                return True
            else:
                print(f"❌ List analyses failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ List analyses error: {e}")
            return False
    
    async def wait_for_analysis_completion(self, analysis_id: str, max_wait: int = 120) -> bool:
        """Wait for analysis to complete."""
        print(f"⏳ Waiting for analysis {analysis_id} to complete...")
        
        for i in range(max_wait):
            try:
                response = await self.client.get(
                    f"{self.base_url}/results/{analysis_id}",
                    params={"api_key": self.api_key}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    
                    if status == "completed":
                        print("✅ Analysis completed successfully")
                        return True
                    elif status == "failed":
                        print(f"❌ Analysis failed: {data.get('error_message')}")
                        return False
                    else:
                        print(f"   Status: {status} (waiting...)")
                        await asyncio.sleep(1)
                else:
                    print(f"   Error checking status: {response.status_code}")
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"   Error checking status: {e}")
                await asyncio.sleep(1)
        
        print("⏰ Analysis timed out")
        return False
    
    async def run_full_test(self) -> bool:
        """Run complete test suite."""
        print("🚀 Starting CrewInsight MVP API Tests")
        print("=" * 50)
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Health check
        total_tests += 1
        if await self.test_health_check():
            tests_passed += 1
        print()
        
        # Test 2: Root endpoint
        total_tests += 1
        if await self.test_root_endpoint():
            tests_passed += 1
        print()
        
        # Test 3: Invalid API key
        total_tests += 1
        if await self.test_invalid_api_key():
            tests_passed += 1
        print()
        
        # Test 4: Start analysis
        total_tests += 1
        analysis_id = await self.test_analyze_endpoint()
        if analysis_id:
            tests_passed += 1
        print()
        
        # Test 5: Wait for completion and get results
        if analysis_id:
            total_tests += 1
            if await self.wait_for_analysis_completion(analysis_id):
                tests_passed += 1
            print()
            
            total_tests += 1
            if await self.test_results_endpoint(analysis_id):
                tests_passed += 1
            print()
        
        # Test 6: List analyses
        total_tests += 1
        if await self.test_list_analyses():
            tests_passed += 1
        print()
        
        # Summary
        print("=" * 50)
        print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed == total_tests:
            print("🎉 All tests passed! MVP is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Check the logs above.")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    """Run the test suite."""
    tester = CrewInsightTester()
    
    try:
        success = await tester.run_full_test()
        exit_code = 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        exit_code = 1
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        exit_code = 1
    finally:
        await tester.close()
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
