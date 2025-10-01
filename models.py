"""Data models for CrewInsight MVP."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class MarketRegion(str, Enum):
    """Supported market regions."""
    US = "US"
    EU = "EU"
    ASIA = "ASIA"
    GLOBAL = "GLOBAL"


class TimeFrame(str, Enum):
    """Supported time frames."""
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1m"
    QUARTERLY = "3m"
    YEARLY = "1y"


class AnalysisRequest(BaseModel):
    """Request model for market analysis."""
    market: str = Field(..., description="Market or sector to analyze (e.g., 'technology', 'finance')")
    region: MarketRegion = Field(..., description="Geographic region for analysis")
    timeframe: TimeFrame = Field(..., description="Time period for analysis")
    api_key: str = Field(..., description="API key for authentication")


class TrendData(BaseModel):
    """Individual trend data."""
    trend_name: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_data: List[str] = Field(default_factory=list)
    impact: str = Field(..., description="Expected impact: positive, negative, neutral")


class MarketData(BaseModel):
    """Market data from various sources."""
    source: str
    data_type: str
    timestamp: datetime
    raw_data: Dict[str, Any]
    processed_data: Dict[str, Any]


class AnalysisResult(BaseModel):
    """Complete analysis result."""
    id: str
    request: AnalysisRequest
    status: str = Field(..., description="Status: processing, completed, failed")
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    # Analysis components
    market_data: List[MarketData] = Field(default_factory=list)
    trends: List[TrendData] = Field(default_factory=list)
    summary: Optional[str] = None
    
    # Metadata
    processing_time: Optional[float] = None
    error_message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
