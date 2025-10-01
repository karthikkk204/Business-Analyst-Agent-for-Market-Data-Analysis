#!/usr/bin/env python3
"""Startup script for CrewInsight MVP."""

import os
import sys
import subprocess
from pathlib import Path


def check_requirements():
    """Check if requirements are installed."""
    try:
        import fastapi
        import uvicorn
        import openai
        import httpx
        import pandas
        import numpy
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("💡 Install requirements with: pip install -r requirements.txt")
        return False


def check_env_file():
    """Check if .env file exists."""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
        return True
    else:
        print("⚠️  .env file not found")
        print("💡 Create a .env file with your API keys:")
        print("   OPENAI_API_KEY=your_openai_api_key_here")
        print("   API_KEY=crewinsight-mvp-2024")
        print("   (Optional: ALPHA_VANTAGE_API_KEY, NEWS_API_KEY, FINNHUB_API_KEY)")
        return False


def main():
    """Main startup function."""
    print("🚀 CrewInsight MVP - Business Analyst Agent")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment file
    env_exists = check_env_file()
    
    print("\n🔧 Configuration:")
    print(f"   Environment file: {'✅ Found' if env_exists else '⚠️  Missing'}")
    print("   Default API key: crewinsight-mvp-2024")
    print("   Server: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    
    print("\n📚 Available commands:")
    print("   python run.py          - Start the server")
    print("   python test_api.py     - Run API tests")
    print("   python example_usage.py - See example usage")
    
    if not env_exists:
        print("\n⚠️  Warning: Without .env file, some features may use mock data")
    
    print("\n🎯 Ready to start! Run: python run.py")


if __name__ == "__main__":
    main()
