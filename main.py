"""Main FastAPI application for CrewInsight MVP."""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from models import AnalysisRequest, AnalysisResult, ErrorResponse, MarketRegion, TimeFrame
from storage import storage
from data_collectors import DataCollectorManager
from trend_analyzer import TrendAnalyzer
from summarizer import MarketSummarizer
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CrewInsight MVP",
    description="Business Analyst Agent for Market Data Analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
data_collector_manager = DataCollectorManager()
trend_analyzer = TrendAnalyzer()
summarizer = MarketSummarizer()


def verify_api_key(api_key: str) -> bool:
    """Verify API key for authentication."""
    return api_key == settings.api_key


async def authenticate_request(api_key: str) -> bool:
    """Authenticate API request."""
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return True


@app.get("/")
async def root():
    """Root endpoint - redirect to UI."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "message": "CrewInsight MVP - Business Analyst Agent",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "POST /analyze",
            "results": "GET /results/{id}",
            "health": "GET /health",
            "docs": "GET /docs",
            "ui": "GET /static/index.html"
        },
        "supported_regions": [region.value for region in MarketRegion],
        "supported_timeframes": [timeframe.value for timeframe in TimeFrame]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test OpenAI connection
        openai_status = await summarizer.test_connection()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "openai": "connected" if openai_status else "disconnected",
                "storage": "active",
                "data_collectors": "ready"
            },
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.post("/analyze", response_model=Dict[str, str])
async def analyze_market(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Start market analysis process."""
    try:
        # Authenticate request
        await authenticate_request(request.api_key)
        
        # Validate request
        if not request.market.strip():
            raise HTTPException(
                status_code=400,
                detail="Market parameter cannot be empty"
            )
        
        logger.info(f"Starting analysis for {request.market} in {request.region} over {request.timeframe}")
        
        # Create analysis record
        analysis_id = storage.create_analysis(request)
        
        # Start background analysis
        background_tasks.add_task(
            perform_analysis,
            analysis_id,
            request.market,
            request.region,
            request.timeframe
        )
        
        return {
            "analysis_id": analysis_id,
            "status": "processing",
            "message": "Analysis started successfully",
            "estimated_completion": "30-60 seconds"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start analysis: {str(e)}"
        )


@app.get("/results/{analysis_id}", response_model=AnalysisResult)
async def get_results(analysis_id: str, api_key: str):
    """Get analysis results by ID."""
    try:
        # Authenticate request
        await authenticate_request(api_key)
        
        # Get analysis result
        result = storage.get_analysis(analysis_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found or expired"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve results: {str(e)}"
        )


@app.get("/results", response_model=List[AnalysisResult])
async def list_recent_analyses(api_key: str, limit: int = 10):
    """List recent analyses."""
    try:
        # Authenticate request
        await authenticate_request(api_key)
        
        # Get recent analyses
        analyses = storage.list_analyses(limit=limit)
        
        return analyses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing analyses: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list analyses: {str(e)}"
        )


@app.delete("/results/{analysis_id}")
async def delete_analysis(analysis_id: str, api_key: str):
    """Delete analysis result."""
    try:
        # Authenticate request
        await authenticate_request(api_key)
        
        # Delete analysis
        success = storage.delete_analysis(analysis_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found"
            )
        
        return {"message": "Analysis deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete analysis: {str(e)}"
        )


async def perform_analysis(analysis_id: str, market: str, region: MarketRegion, timeframe: TimeFrame):
    """Perform the actual market analysis in background."""
    start_time = time.time()
    
    try:
        logger.info(f"Starting analysis {analysis_id} for {market}")
        
        # Update status to processing
        storage.update_analysis(analysis_id, status="processing")
        
        # Step 1: Collect market data
        logger.info(f"Collecting data for {market}")
        market_data = await data_collector_manager.collect_all_data(market, region, timeframe)
        
        if not market_data:
            raise Exception("No market data collected")
        
        logger.info(f"Collected {len(market_data)} data points")
        
        # Step 2: Analyze trends
        logger.info(f"Analyzing trends for {market}")
        trends = trend_analyzer.analyze_trends(market_data, market, region, timeframe)
        
        if not trends:
            raise Exception("No trends identified")
        
        logger.info(f"Identified {len(trends)} trends")
        
        # Step 3: Generate summary
        logger.info(f"Generating summary for {market}")
        summary = await summarizer.generate_summary(market_data, trends, market, region, timeframe)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Update analysis with results
        storage.update_analysis(
            analysis_id,
            status="completed",
            market_data=market_data,
            trends=trends,
            summary=summary,
            processing_time=processing_time
        )
        
        logger.info(f"Analysis {analysis_id} completed in {processing_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {e}")
        
        # Update analysis with error
        storage.update_analysis(
            analysis_id,
            status="failed",
            error_message=str(e),
            processing_time=time.time() - start_time
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail="An unexpected error occurred"
        ).dict()
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
