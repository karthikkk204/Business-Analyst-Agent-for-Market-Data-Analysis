"""Trend analysis engine for identifying market trends."""

import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
import statistics

from models import MarketData, TrendData, MarketRegion, TimeFrame

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyzes market data to identify key trends."""
    
    def __init__(self):
        self.min_confidence_threshold = 0.3
        self.max_trends = 5
    
    def analyze_trends(self, market_data: List[MarketData], market: str, region: MarketRegion, timeframe: TimeFrame) -> List[TrendData]:
        """Analyze market data and identify key trends."""
        logger.info(f"Analyzing trends for {market} in {region} over {timeframe}")
        
        trends = []
        
        # Analyze different types of trends
        price_trends = self._analyze_price_trends(market_data)
        sentiment_trends = self._analyze_sentiment_trends(market_data)
        economic_trends = self._analyze_economic_trends(market_data)
        sector_trends = self._analyze_sector_trends(market_data, market)
        
        # Combine all trends
        all_trends = price_trends + sentiment_trends + economic_trends + sector_trends
        
        # Filter and rank trends by confidence
        filtered_trends = [trend for trend in all_trends if trend.confidence >= self.min_confidence_threshold]
        sorted_trends = sorted(filtered_trends, key=lambda x: x.confidence, reverse=True)
        
        # Return top trends
        return sorted_trends[:self.max_trends]
    
    def _analyze_price_trends(self, market_data: List[MarketData]) -> List[TrendData]:
        """Analyze price-related trends."""
        trends = []
        
        for data in market_data:
            if data.source == "Alpha Vantage" and "price_trend" in data.processed_data:
                price_data = data.processed_data
                
                # Price movement trend
                if price_data.get("price_trend") == "up":
                    trend = TrendData(
                        trend_name="Positive Price Momentum",
                        description=f"Market showing upward price movement with {price_data.get('price_change_percent', 0):.2f}% change",
                        confidence=min(0.9, abs(price_data.get('price_change_percent', 0)) / 10),
                        supporting_data=[
                            f"Price change: {price_data.get('price_change_percent', 0):.2f}%",
                            f"Volatility: {price_data.get('volatility', 0):.2f}%"
                        ],
                        impact="positive"
                    )
                    trends.append(trend)
                
                elif price_data.get("price_trend") == "down":
                    trend = TrendData(
                        trend_name="Negative Price Momentum",
                        description=f"Market showing downward price movement with {price_data.get('price_change_percent', 0):.2f}% change",
                        confidence=min(0.9, abs(price_data.get('price_change_percent', 0)) / 10),
                        supporting_data=[
                            f"Price change: {price_data.get('price_change_percent', 0):.2f}%",
                            f"Volatility: {price_data.get('volatility', 0):.2f}%"
                        ],
                        impact="negative"
                    )
                    trends.append(trend)
                
                # Volatility trend
                volatility = price_data.get('volatility', 0)
                if volatility > 20:
                    trend = TrendData(
                        trend_name="High Market Volatility",
                        description=f"Market experiencing high volatility at {volatility:.2f}%",
                        confidence=min(0.8, volatility / 30),
                        supporting_data=[
                            f"Volatility level: {volatility:.2f}%",
                            f"Data points analyzed: {price_data.get('data_points', 0)}"
                        ],
                        impact="neutral"
                    )
                    trends.append(trend)
        
        return trends
    
    def _analyze_sentiment_trends(self, market_data: List[MarketData]) -> List[TrendData]:
        """Analyze sentiment-related trends from news data."""
        trends = []
        
        for data in market_data:
            if data.source == "Financial News" and "sentiment_trend" in data.processed_data:
                sentiment_data = data.processed_data
                
                sentiment = sentiment_data.get("sentiment_trend", "neutral")
                avg_sentiment = sentiment_data.get("avg_sentiment", 0)
                news_volume = sentiment_data.get("news_volume", 0)
                
                if sentiment == "positive" and avg_sentiment > 0.2:
                    trend = TrendData(
                        trend_name="Positive Market Sentiment",
                        description=f"Strong positive sentiment in news coverage with {news_volume} articles analyzed",
                        confidence=min(0.9, avg_sentiment * 2),
                        supporting_data=[
                            f"Average sentiment score: {avg_sentiment:.3f}",
                            f"News volume: {news_volume} articles",
                            f"Top themes: {', '.join(sentiment_data.get('top_themes', [])[:3])}"
                        ],
                        impact="positive"
                    )
                    trends.append(trend)
                
                elif sentiment == "negative" and avg_sentiment < -0.2:
                    trend = TrendData(
                        trend_name="Negative Market Sentiment",
                        description=f"Negative sentiment in news coverage with {news_volume} articles analyzed",
                        confidence=min(0.9, abs(avg_sentiment) * 2),
                        supporting_data=[
                            f"Average sentiment score: {avg_sentiment:.3f}",
                            f"News volume: {news_volume} articles",
                            f"Top themes: {', '.join(sentiment_data.get('top_themes', [])[:3])}"
                        ],
                        impact="negative"
                    )
                    trends.append(trend)
                
                # News volume trend
                if news_volume > 50:
                    trend = TrendData(
                        trend_name="High News Volume",
                        description=f"Significant media attention with {news_volume} articles in the timeframe",
                        confidence=min(0.7, news_volume / 100),
                        supporting_data=[
                            f"Article count: {news_volume}",
                            f"Sentiment trend: {sentiment}"
                        ],
                        impact="neutral"
                    )
                    trends.append(trend)
        
        return trends
    
    def _analyze_economic_trends(self, market_data: List[MarketData]) -> List[TrendData]:
        """Analyze economic indicator trends."""
        trends = []
        
        for data in market_data:
            if data.source == "Economic Indicators":
                economic_data = data.processed_data
                
                # Economic health trend
                health = economic_data.get("economic_health", "unknown")
                if health == "good":
                    trend = TrendData(
                        trend_name="Strong Economic Fundamentals",
                        description="Economic indicators show positive fundamentals supporting market growth",
                        confidence=0.8,
                        supporting_data=[
                            f"Economic health: {health}",
                            f"Growth trend: {economic_data.get('growth_trend', 'unknown')}",
                            f"Key risks: {', '.join(economic_data.get('key_risks', []))}"
                        ],
                        impact="positive"
                    )
                    trends.append(trend)
                
                elif health == "moderate":
                    trend = TrendData(
                        trend_name="Mixed Economic Signals",
                        description="Economic indicators show mixed signals with moderate growth prospects",
                        confidence=0.6,
                        supporting_data=[
                            f"Economic health: {health}",
                            f"Growth trend: {economic_data.get('growth_trend', 'unknown')}",
                            f"Market conditions: {economic_data.get('market_conditions', 'unknown')}"
                        ],
                        impact="neutral"
                    )
                    trends.append(trend)
                
                # Market conditions trend
                conditions = economic_data.get("market_conditions", "unknown")
                if conditions == "volatile":
                    trend = TrendData(
                        trend_name="Volatile Market Conditions",
                        description="Economic indicators suggest increased market volatility",
                        confidence=0.7,
                        supporting_data=[
                            f"Market conditions: {conditions}",
                            f"Inflation pressure: {economic_data.get('inflation_pressure', 'unknown')}",
                            f"Key risks: {', '.join(economic_data.get('key_risks', []))}"
                        ],
                        impact="negative"
                    )
                    trends.append(trend)
        
        return trends
    
    def _analyze_sector_trends(self, market_data: List[MarketData], market: str) -> List[TrendData]:
        """Analyze sector-specific trends."""
        trends = []
        
        # Look for sector-specific data
        sector_data = None
        for data in market_data:
            if "sector" in data.processed_data:
                sector_data = data.processed_data
                break
        
        if sector_data:
            sector = sector_data.get("sector", market.title())
            pe_ratio = sector_data.get("pe_ratio")
            
            if pe_ratio:
                try:
                    pe_value = float(pe_ratio)
                    if pe_value > 30:
                        trend = TrendData(
                            trend_name="High Valuation Sector",
                            description=f"{sector} sector showing high valuations with P/E ratio of {pe_value}",
                            confidence=0.7,
                            supporting_data=[
                                f"P/E ratio: {pe_value}",
                                f"Sector: {sector}",
                                f"Market cap: {sector_data.get('market_cap', 'N/A')}"
                            ],
                            impact="neutral"
                        )
                        trends.append(trend)
                    
                    elif pe_value < 15:
                        trend = TrendData(
                            trend_name="Undervalued Sector Opportunity",
                            description=f"{sector} sector appears undervalued with P/E ratio of {pe_value}",
                            confidence=0.6,
                            supporting_data=[
                                f"P/E ratio: {pe_value}",
                                f"Sector: {sector}",
                                f"Market cap: {sector_data.get('market_cap', 'N/A')}"
                            ],
                            impact="positive"
                        )
                        trends.append(trend)
                
                except (ValueError, TypeError):
                    pass
        
        # Market-specific trend analysis
        market_trend = self._get_market_specific_trend(market, market_data)
        if market_trend:
            trends.append(market_trend)
        
        return trends
    
    def _get_market_specific_trend(self, market: str, market_data: List[MarketData]) -> TrendData:
        """Get market-specific trend based on the sector."""
        market_lower = market.lower()
        
        # Technology sector trends
        if "tech" in market_lower or "technology" in market_lower:
            return TrendData(
                trend_name="Technology Innovation Drive",
                description="Technology sector continues to drive innovation with strong growth potential",
                confidence=0.8,
                supporting_data=[
                    "High R&D investment",
                    "Digital transformation acceleration",
                    "AI and automation adoption"
                ],
                impact="positive"
            )
        
        # Finance sector trends
        elif "finance" in market_lower or "financial" in market_lower:
            return TrendData(
                trend_name="Financial Services Evolution",
                description="Financial services sector adapting to digital transformation and regulatory changes",
                confidence=0.7,
                supporting_data=[
                    "Fintech disruption",
                    "Regulatory compliance focus",
                    "Interest rate sensitivity"
                ],
                impact="neutral"
            )
        
        # Healthcare sector trends
        elif "health" in market_lower or "healthcare" in market_lower:
            return TrendData(
                trend_name="Healthcare Innovation Growth",
                description="Healthcare sector benefiting from innovation and demographic trends",
                confidence=0.8,
                supporting_data=[
                    "Aging population",
                    "Medical technology advances",
                    "Regulatory approval pipeline"
                ],
                impact="positive"
            )
        
        # Energy sector trends
        elif "energy" in market_lower:
            return TrendData(
                trend_name="Energy Transition Impact",
                description="Energy sector navigating transition to renewable sources",
                confidence=0.7,
                supporting_data=[
                    "Renewable energy growth",
                    "Fossil fuel transition",
                    "Geopolitical factors"
                ],
                impact="neutral"
            )
        
        # Default trend for other sectors
        else:
            return TrendData(
                trend_name="Sector-Specific Opportunities",
                description=f"{market.title()} sector showing sector-specific growth opportunities",
                confidence=0.6,
                supporting_data=[
                    "Market-specific factors",
                    "Regional economic conditions",
                    "Industry dynamics"
                ],
                impact="positive"
            )
    
    def _calculate_trend_confidence(self, supporting_data: List[str], data_quality: float = 1.0) -> float:
        """Calculate confidence score for a trend based on supporting data."""
        base_confidence = min(0.9, len(supporting_data) * 0.2)
        return base_confidence * data_quality
    
    def _get_trend_impact(self, trend_type: str, magnitude: float) -> str:
        """Determine the impact of a trend (positive, negative, neutral)."""
        if trend_type in ["price_momentum", "sentiment", "economic_health"]:
            return "positive" if magnitude > 0 else "negative"
        elif trend_type in ["volatility", "uncertainty"]:
            return "negative"
        else:
            return "neutral"
