"""Example usage of CrewInsight MVP API."""

import asyncio
import httpx
import json
from typing import Dict, Any


async def analyze_market_example():
    """Example of how to use the CrewInsight API."""
    
    base_url = "http://localhost:8000"
    api_key = "crewinsight-mvp-2024"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        print("🔍 CrewInsight MVP - Market Analysis Example")
        print("=" * 50)
        
        # Example 1: Technology sector analysis
        print("\n📊 Example 1: Technology Sector Analysis")
        print("-" * 40)
        
        analysis_request = {
            "market": "technology",
            "region": "US",
            "timeframe": "1m",
            "api_key": api_key
        }
        
        try:
            # Start analysis
            response = await client.post(f"{base_url}/analyze", json=analysis_request)
            
            if response.status_code == 200:
                data = response.json()
                analysis_id = data["analysis_id"]
                print(f"✅ Analysis started: {analysis_id}")
                
                # Wait for completion
                print("⏳ Waiting for analysis to complete...")
                for i in range(60):  # Wait up to 60 seconds
                    await asyncio.sleep(1)
                    
                    result_response = await client.get(
                        f"{base_url}/results/{analysis_id}",
                        params={"api_key": api_key}
                    )
                    
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        status = result_data["status"]
                        
                        if status == "completed":
                            print("✅ Analysis completed!")
                            print(f"📈 Trends identified: {len(result_data['trends'])}")
                            print(f"📝 Summary length: {len(result_data['summary'])} characters")
                            print(f"⏱️  Processing time: {result_data['processing_time']:.2f} seconds")
                            
                            # Display trends
                            print("\n🎯 Key Trends:")
                            for i, trend in enumerate(result_data['trends'], 1):
                                impact_emoji = {"positive": "📈", "negative": "📉", "neutral": "➡️"}.get(trend['impact'], "➡️")
                                print(f"   {i}. {impact_emoji} {trend['trend_name']}")
                                print(f"      Confidence: {trend['confidence']:.1%}")
                                print(f"      {trend['description']}")
                            
                            # Display summary
                            print(f"\n📋 Summary:")
                            print(f"   {result_data['summary'][:200]}...")
                            break
                            
                        elif status == "failed":
                            print(f"❌ Analysis failed: {result_data.get('error_message')}")
                            break
                        else:
                            print(f"   Status: {status} (waiting...)")
                    else:
                        print(f"   Error checking status: {result_response.status_code}")
                
                else:
                    print("⏰ Analysis timed out")
            
            else:
                print(f"❌ Failed to start analysis: {response.status_code}")
                print(f"   Response: {response.text}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Example 2: Finance sector analysis
        print("\n\n📊 Example 2: Finance Sector Analysis")
        print("-" * 40)
        
        finance_request = {
            "market": "finance",
            "region": "US",
            "timeframe": "1w",
            "api_key": api_key
        }
        
        try:
            response = await client.post(f"{base_url}/analyze", json=finance_request)
            
            if response.status_code == 200:
                data = response.json()
                analysis_id = data["analysis_id"]
                print(f"✅ Finance analysis started: {analysis_id}")
                
                # Quick check (don't wait for completion in example)
                await asyncio.sleep(2)
                result_response = await client.get(
                    f"{base_url}/results/{analysis_id}",
                    params={"api_key": api_key}
                )
                
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    print(f"   Current status: {result_data['status']}")
                else:
                    print(f"   Error checking status: {result_response.status_code}")
            
            else:
                print(f"❌ Failed to start finance analysis: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Example 3: List recent analyses
        print("\n\n📋 Example 3: List Recent Analyses")
        print("-" * 40)
        
        try:
            response = await client.get(
                f"{base_url}/results",
                params={"api_key": api_key, "limit": 5}
            )
            
            if response.status_code == 200:
                analyses = response.json()
                print(f"✅ Found {len(analyses)} recent analyses:")
                
                for i, analysis in enumerate(analyses, 1):
                    print(f"   {i}. {analysis['id'][:8]}... - {analysis['status']} - {analysis['request']['market']}")
            
            else:
                print(f"❌ Failed to list analyses: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Example 4: Health check
        print("\n\n🏥 Example 4: Health Check")
        print("-" * 40)
        
        try:
            response = await client.get(f"{base_url}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                print("✅ System health check:")
                print(f"   Status: {health_data['status']}")
                print(f"   Services: {health_data['services']}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Example completed!")
        print("💡 Try running your own analysis with different markets and timeframes!")


async def quick_test():
    """Quick test to verify API is working."""
    
    base_url = "http://localhost:8000"
    api_key = "crewinsight-mvp-2024"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Test health
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ API is running and healthy")
                return True
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            print("💡 Make sure the server is running with: python run.py")
            return False


if __name__ == "__main__":
    print("🚀 CrewInsight MVP - Example Usage")
    print("Make sure the server is running first: python run.py")
    print()
    
    # Quick connection test
    if asyncio.run(quick_test()):
        print("\nRunning full example...")
        asyncio.run(analyze_market_example())
    else:
        print("\n❌ Cannot proceed - API is not available")
