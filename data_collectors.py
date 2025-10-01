"""Data collectors for market data from various sources."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import httpx
import pandas as pd

from models import MarketData, MarketRegion, TimeFrame
from config import settings

logger = logging.getLogger(__name__)


class BaseDataCollector:
    """Base class for data collectors."""
    
    def __init__(self, name: str):
        self.name = name
        self.timeout = settings.request_timeout
    
    async def collect_data(self, market: str, region: MarketRegion, timeframe: TimeFrame) -> List[MarketData]:
        """Collect market data. Must be implemented by subclasses."""
        raise NotImplementedError
    
    def _create_market_data(self, raw_data: Dict[str, Any], processed_data: Dict[str, Any]) -> MarketData:
        """Create MarketData object."""
        return MarketData(
            source=self.name,
            data_type="market_data",
            timestamp=datetime.now(),
            raw_data=raw_data,
            processed_data=processed_data
        )


class AlphaVantageCollector(BaseDataCollector):
    """Collector for Alpha Vantage financial data."""
    
    def __init__(self):
        super().__init__("Alpha Vantage")
        self.api_key = settings.alpha_vantage_api_key
        self.base_url = "https://www.alphavantage.co/query"
    
    async def collect_data(self, market: str, region: MarketRegion, timeframe: TimeFrame) -> List[MarketData]:
        """Collect data from Alpha Vantage."""
        if not self.api_key:
            logger.warning("Alpha Vantage API key not provided, using mock data")
            return self._get_mock_data(market, region, timeframe)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get market overview data
                overview_data = await self._get_market_overview(client, market)
                
                # Get time series data
                timeseries_data = await self._get_timeseries_data(client, market, timeframe)
                
                results = []
                if overview_data:
                    results.append(overview_data)
                if timeseries_data:
                    results.append(timeseries_data)
                
                return results
                
        except Exception as e:
            logger.error(f"Error collecting Alpha Vantage data: {e}")
            return self._get_mock_data(market, region, timeframe)
    
    async def _get_market_overview(self, client: httpx.AsyncClient, market: str) -> Optional[MarketData]:
        """Get market overview data."""
        try:
            params = {
                "function": "OVERVIEW",
                "symbol": self._get_symbol_for_market(market),
                "apikey": self.api_key
            }
            
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "Error Message" in data:
                logger.warning(f"Alpha Vantage error: {data['Error Message']}")
                return None
            
            processed_data = {
                "market_cap": data.get("MarketCapitalization"),
                "pe_ratio": data.get("PERatio"),
                "sector": data.get("Sector"),
                "industry": data.get("Industry"),
                "description": data.get("Description", "")[:500]  # Truncate for storage
            }
            
            return self._create_market_data(data, processed_data)
            
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return None
    
    async def _get_timeseries_data(self, client: httpx.AsyncClient, market: str, timeframe: TimeFrame) -> Optional[MarketData]:
        """Get time series data."""
        try:
            function_map = {
                TimeFrame.DAILY: "TIME_SERIES_DAILY",
                TimeFrame.WEEKLY: "TIME_SERIES_WEEKLY",
                TimeFrame.MONTHLY: "TIME_SERIES_MONTHLY"
            }
            
            function = function_map.get(timeframe, "TIME_SERIES_DAILY")
            
            params = {
                "function": function,
                "symbol": self._get_symbol_for_market(market),
                "apikey": self.api_key,
                "outputsize": "compact"
            }
            
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "Error Message" in data:
                logger.warning(f"Alpha Vantage timeseries error: {data['Error Message']}")
                return None
            
            # Process time series data
            time_series_key = list(data.keys())[1]  # Skip metadata key
            time_series = data[time_series_key]
            
            # Calculate basic statistics
            prices = [float(day_data["4. close"]) for day_data in time_series.values()]
            processed_data = {
                "price_trend": "up" if prices[0] > prices[-1] else "down",
                "price_change_percent": ((prices[0] - prices[-1]) / prices[-1]) * 100,
                "volatility": self._calculate_volatility(prices),
                "data_points": len(prices)
            }
            
            return self._create_market_data(data, processed_data)
            
        except Exception as e:
            logger.error(f"Error getting timeseries data: {e}")
            return None
    
    def _get_symbol_for_market(self, market: str) -> str:
        """Get stock symbol for market/sector."""
        symbol_map = {
            "technology": "AAPL",
            "finance": "JPM",
            "healthcare": "JNJ",
            "energy": "XOM",
            "consumer": "WMT",
            "default": "SPY"  # S&P 500 ETF as default
        }
        return symbol_map.get(market.lower(), symbol_map["default"])
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility."""
        if len(prices) < 2:
            return 0.0
        
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        return float(pd.Series(returns).std()) * 100  # Convert to percentage
    
    def _get_mock_data(self, market: str, region: MarketRegion, timeframe: TimeFrame) -> List[MarketData]:
        """Generate mock data when API is unavailable."""
        mock_overview = {
            "Symbol": self._get_symbol_for_market(market),
            "Name": f"{market.title()} Sector",
            "Sector": market.title(),
            "MarketCapitalization": "1000000000",
            "PERatio": "25.5",
            "Description": f"Mock data for {market} sector analysis"
        }
        
        processed_overview = {
            "market_cap": "1B",
            "pe_ratio": "25.5",
            "sector": market.title(),
            "industry": f"{market.title()} Industry",
            "description": f"Mock data for {market} sector analysis"
        }
        
        mock_timeseries = {
            "Meta Data": {"Symbol": self._get_symbol_for_market(market)},
            "Time Series": {
                "2024-01-01": {"4. close": "150.00"},
                "2024-01-02": {"4. close": "152.50"},
                "2024-01-03": {"4. close": "151.25"}
            }
        }
        
        processed_timeseries = {
            "price_trend": "up",
            "price_change_percent": 0.83,
            "volatility": 1.2,
            "data_points": 3
        }
        
        return [
            self._create_market_data(mock_overview, processed_overview),
            self._create_market_data(mock_timeseries, processed_timeseries)
        ]


class NewsCollector(BaseDataCollector):
    """Collector for financial news data."""
    
    def __init__(self):
        super().__init__("Financial News")
        self.api_key = settings.news_api_key
        self.base_url = "https://newsapi.org/v2/everything"
    
    async def collect_data(self, market: str, region: MarketRegion, timeframe: TimeFrame) -> List[MarketData]:
        """Collect financial news data."""
        if not self.api_key:
            logger.warning("News API key not provided, using mock data")
            return self._get_mock_news_data(market, region, timeframe)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Calculate date range based on timeframe
                end_date = datetime.now()
                start_date = self._get_start_date(end_date, timeframe)
                
                params = {
                    "q": f"{market} market",
                    "from": start_date.strftime("%Y-%m-%d"),
                    "to": end_date.strftime("%Y-%m-%d"),
                    "sortBy": "publishedAt",
                    "language": "en",
                    "pageSize": 20,
                    "apiKey": self.api_key
                }
                
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != "ok":
                    logger.warning(f"News API error: {data.get('message', 'Unknown error')}")
                    return self._get_mock_news_data(market, region, timeframe)
                
                return self._process_news_data(data, market)
                
        except Exception as e:
            logger.error(f"Error collecting news data: {e}")
            return self._get_mock_news_data(market, region, timeframe)
    
    def _get_start_date(self, end_date: datetime, timeframe: TimeFrame) -> datetime:
        """Get start date based on timeframe."""
        timeframe_days = {
            TimeFrame.DAILY: 1,
            TimeFrame.WEEKLY: 7,
            TimeFrame.MONTHLY: 30,
            TimeFrame.QUARTERLY: 90,
            TimeFrame.YEARLY: 365
        }
        days = timeframe_days.get(timeframe, 7)
        return end_date - timedelta(days=days)
    
    def _process_news_data(self, data: Dict[str, Any], market: str) -> List[MarketData]:
        """Process news data and extract sentiment/trends."""
        articles = data.get("articles", [])
        
        # Analyze sentiment and extract key themes
        sentiment_scores = []
        key_themes = []
        
        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            
            # Simple sentiment analysis (positive/negative keywords)
            sentiment = self._analyze_sentiment(title + " " + description)
            sentiment_scores.append(sentiment)
            
            # Extract key themes
            themes = self._extract_themes(title + " " + description)
            key_themes.extend(themes)
        
        # Calculate overall sentiment
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        # Get most common themes
        theme_counts = {}
        for theme in key_themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        processed_data = {
            "article_count": len(articles),
            "avg_sentiment": avg_sentiment,
            "sentiment_trend": "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral",
            "top_themes": [theme for theme, count in top_themes],
            "news_volume": len(articles)
        }
        
        return [self._create_market_data(data, processed_data)]
    
    def _analyze_sentiment(self, text: str) -> float:
        """Simple sentiment analysis using keyword matching."""
        positive_words = ["growth", "profit", "gain", "rise", "increase", "positive", "strong", "up", "bullish"]
        negative_words = ["decline", "loss", "fall", "drop", "decrease", "negative", "weak", "down", "bearish"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_words
    
    def _extract_themes(self, text: str) -> List[str]:
        """Extract key themes from text."""
        themes = []
        text_lower = text.lower()
        
        theme_keywords = {
            "earnings": ["earnings", "revenue", "profit", "quarterly"],
            "regulation": ["regulation", "policy", "government", "compliance"],
            "innovation": ["innovation", "technology", "digital", "ai", "automation"],
            "competition": ["competition", "market share", "rival", "competitor"],
            "mergers": ["merger", "acquisition", "deal", "buyout"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                themes.append(theme)
        
        return themes
    
    def _get_mock_news_data(self, market: str, region: MarketRegion, timeframe: TimeFrame) -> List[MarketData]:
        """Generate mock news data."""
        mock_data = {
            "status": "ok",
            "totalResults": 15,
            "articles": [
                {
                    "title": f"{market.title()} sector shows strong growth",
                    "description": f"Recent developments in {market} indicate positive trends",
                    "publishedAt": datetime.now().isoformat()
                },
                {
                    "title": f"Market analysis: {market} outlook remains optimistic",
                    "description": f"Experts predict continued growth in {market} sector",
                    "publishedAt": (datetime.now() - timedelta(days=1)).isoformat()
                }
            ]
        }
        
        processed_data = {
            "article_count": 15,
            "avg_sentiment": 0.3,
            "sentiment_trend": "positive",
            "top_themes": ["earnings", "innovation", "growth"],
            "news_volume": 15
        }
        
        return [self._create_market_data(mock_data, processed_data)]


class EconomicDataCollector(BaseDataCollector):
    """Collector for economic indicators and market data."""
    
    def __init__(self):
        super().__init__("Economic Indicators")
    
    async def collect_data(self, market: str, region: MarketRegion, timeframe: TimeFrame) -> List[MarketData]:
        """Collect economic indicator data."""
        try:
            # Simulate economic data collection
            economic_data = await self._get_economic_indicators(market, region, timeframe)
            return [economic_data]
            
        except Exception as e:
            logger.error(f"Error collecting economic data: {e}")
            return self._get_mock_economic_data(market, region, timeframe)
    
    async def _get_economic_indicators(self, market: str, region: MarketRegion, timeframe: TimeFrame) -> MarketData:
        """Get economic indicators (mock implementation)."""
        # In a real implementation, this would fetch from economic data APIs
        # like FRED (Federal Reserve Economic Data), World Bank, etc.
        
        raw_data = {
            "gdp_growth": 2.5,
            "inflation_rate": 3.2,
            "unemployment_rate": 4.1,
            "interest_rate": 5.25,
            "market_volatility": 18.5
        }
        
        processed_data = {
            "economic_health": "moderate",
            "growth_trend": "stable",
            "inflation_pressure": "moderate",
            "market_conditions": "volatile",
            "key_risks": ["inflation", "interest_rates"]
        }
        
        return self._create_market_data(raw_data, processed_data)
    
    def _get_mock_economic_data(self, market: str, region: MarketRegion, timeframe: TimeFrame) -> List[MarketData]:
        """Generate mock economic data."""
        raw_data = {
            "gdp_growth": 2.8,
            "inflation_rate": 2.9,
            "unemployment_rate": 3.8,
            "interest_rate": 5.0,
            "market_volatility": 15.2
        }
        
        processed_data = {
            "economic_health": "good",
            "growth_trend": "positive",
            "inflation_pressure": "low",
            "market_conditions": "stable",
            "key_risks": ["geopolitical", "supply_chain"]
        }
        
        return [self._create_market_data(raw_data, processed_data)]


class DataCollectorManager:
    """Manager for coordinating multiple data collectors."""
    
    def __init__(self):
        self.collectors = [
            AlphaVantageCollector(),
            NewsCollector(),
            EconomicDataCollector()
        ]
    
    async def collect_all_data(self, market: str, region: MarketRegion, timeframe: TimeFrame) -> List[MarketData]:
        """Collect data from all available sources."""
        tasks = []
        
        for collector in self.collectors:
            task = collector.collect_data(market, region, timeframe)
            tasks.append(task)
        
        # Run all collectors concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results and filter out exceptions
        all_data = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Data collector error: {result}")
            elif isinstance(result, list):
                all_data.extend(result)
        
        logger.info(f"Collected {len(all_data)} data points from {len(self.collectors)} sources")
        return all_data
