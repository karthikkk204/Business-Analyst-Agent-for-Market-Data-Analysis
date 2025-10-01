"""Simple script to run the CrewInsight MVP server."""

import uvicorn
from config import settings

if __name__ == "__main__":
    print("🚀 Starting CrewInsight MVP Server")
    print(f"📍 Server will be available at: http://{settings.host}:{settings.port}")
    print(f"📚 API Documentation: http://{settings.host}:{settings.port}/docs")
    print(f"🔍 Health Check: http://{settings.host}:{settings.port}/health")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
