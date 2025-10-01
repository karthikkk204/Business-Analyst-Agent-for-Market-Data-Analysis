"""OpenAI-powered summarization service for market insights."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import openai
from openai import AsyncOpenAI

from models import MarketData, TrendData, MarketRegion, TimeFrame
from config import settings

logger = logging.getLogger(__name__)


class MarketSummarizer:
    """Generates concise market insights using OpenAI."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.max_tokens = 500  # Keep summary under 300 words
        self.model = "gpt-3.5-turbo"
    
    async def generate_summary(
        self, 
        market_data: List[MarketData], 
        trends: List[TrendData], 
        market: str, 
        region: MarketRegion, 
        timeframe: TimeFrame
    ) -> str:
        """Generate a concise summary of market insights."""
        try:
            # Prepare context for the AI
            context = self._prepare_context(market_data, trends, market, region, timeframe)
            
            # Generate summary using OpenAI
            summary = await self._call_openai(context)
            
            # Ensure summary is within word limit
            summary = self._truncate_summary(summary)
            
            logger.info(f"Generated summary for {market} market analysis")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return self._generate_fallback_summary(market_data, trends, market, region, timeframe)
    
    def _prepare_context(self, market_data: List[MarketData], trends: List[TrendData], market: str, region: MarketRegion, timeframe: TimeFrame) -> str:
        """Prepare context for OpenAI summarization."""
        context_parts = []
        
        # Market overview
        context_parts.append(f"Market Analysis: {market.title()} sector in {region.value} region over {timeframe.value} timeframe")
        context_parts.append("")
        
        # Data sources summary
        context_parts.append("Data Sources:")
        for data in market_data:
            source_summary = self._summarize_data_source(data)
            context_parts.append(f"- {data.source}: {source_summary}")
        context_parts.append("")
        
        # Key trends
        context_parts.append("Key Trends Identified:")
        for i, trend in enumerate(trends, 1):
            impact_emoji = {"positive": "📈", "negative": "📉", "neutral": "➡️"}.get(trend.impact, "➡️")
            context_parts.append(f"{i}. {impact_emoji} {trend.trend_name} (Confidence: {trend.confidence:.1%})")
            context_parts.append(f"   {trend.description}")
            if trend.supporting_data:
                context_parts.append(f"   Supporting data: {', '.join(trend.supporting_data[:3])}")
        context_parts.append("")
        
        # Instructions for AI
        context_parts.append("Please provide a concise business summary (max 300 words) that:")
        context_parts.append("1. Highlights the most important trends and their implications")
        context_parts.append("2. Provides actionable insights for business decision-making")
        context_parts.append("3. Uses clear, professional language suitable for executives")
        context_parts.append("4. Focuses on practical implications rather than technical details")
        
        return "\n".join(context_parts)
    
    def _summarize_data_source(self, data: MarketData) -> str:
        """Create a brief summary of data from a source."""
        processed = data.processed_data
        
        if data.source == "Alpha Vantage":
            return f"Price trend: {processed.get('price_trend', 'unknown')}, Volatility: {processed.get('volatility', 0):.1f}%"
        
        elif data.source == "Financial News":
            return f"Sentiment: {processed.get('sentiment_trend', 'neutral')}, Articles: {processed.get('news_volume', 0)}"
        
        elif data.source == "Economic Indicators":
            return f"Economic health: {processed.get('economic_health', 'unknown')}, Growth: {processed.get('growth_trend', 'unknown')}"
        
        else:
            return f"Data points: {len(processed)}"
    
    async def _call_openai(self, context: str) -> str:
        """Call OpenAI API to generate summary."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior business analyst providing concise market insights. Focus on practical implications and actionable recommendations."
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            return response.choices[0].message.content.strip()
            
        except openai.RateLimitError:
            logger.warning("OpenAI rate limit exceeded, using fallback summary")
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {e}")
            raise
    
    def _truncate_summary(self, summary: str) -> str:
        """Ensure summary is within word limit."""
        words = summary.split()
        if len(words) <= 300:
            return summary
        
        # Truncate to 300 words and add ellipsis
        truncated_words = words[:300]
        return " ".join(truncated_words) + "..."
    
    def _generate_fallback_summary(self, market_data: List[MarketData], trends: List[TrendData], market: str, region: MarketRegion, timeframe: TimeFrame) -> str:
        """Generate a fallback summary when OpenAI is unavailable."""
        logger.info("Generating fallback summary")
        
        summary_parts = []
        
        # Header
        summary_parts.append(f"Market Analysis Summary: {market.title()} Sector")
        summary_parts.append(f"Region: {region.value} | Timeframe: {timeframe.value}")
        summary_parts.append("")
        
        # Key findings
        summary_parts.append("Key Findings:")
        
        if trends:
            # Group trends by impact
            positive_trends = [t for t in trends if t.impact == "positive"]
            negative_trends = [t for t in trends if t.impact == "negative"]
            neutral_trends = [t for t in trends if t.impact == "neutral"]
            
            if positive_trends:
                summary_parts.append("📈 Positive Trends:")
                for trend in positive_trends[:2]:  # Top 2 positive trends
                    summary_parts.append(f"• {trend.trend_name}: {trend.description}")
            
            if negative_trends:
                summary_parts.append("📉 Areas of Concern:")
                for trend in negative_trends[:2]:  # Top 2 negative trends
                    summary_parts.append(f"• {trend.trend_name}: {trend.description}")
            
            if neutral_trends:
                summary_parts.append("➡️ Neutral Observations:")
                for trend in neutral_trends[:1]:  # Top 1 neutral trend
                    summary_parts.append(f"• {trend.trend_name}: {trend.description}")
        
        # Data insights
        summary_parts.append("")
        summary_parts.append("Data Insights:")
        
        for data in market_data:
            if data.source == "Alpha Vantage" and "price_trend" in data.processed_data:
                price_data = data.processed_data
                summary_parts.append(f"• Price movement: {price_data.get('price_trend', 'unknown')} ({price_data.get('price_change_percent', 0):.2f}%)")
            
            elif data.source == "Financial News" and "sentiment_trend" in data.processed_data:
                sentiment_data = data.processed_data
                summary_parts.append(f"• Market sentiment: {sentiment_data.get('sentiment_trend', 'neutral')} based on {sentiment_data.get('news_volume', 0)} articles")
            
            elif data.source == "Economic Indicators":
                economic_data = data.processed_data
                summary_parts.append(f"• Economic health: {economic_data.get('economic_health', 'unknown')} with {economic_data.get('growth_trend', 'unknown')} growth trend")
        
        # Recommendations
        summary_parts.append("")
        summary_parts.append("Recommendations:")
        
        if trends:
            high_confidence_trends = [t for t in trends if t.confidence > 0.7]
            if high_confidence_trends:
                summary_parts.append("• Monitor high-confidence trends closely for strategic planning")
            
            positive_trends = [t for t in trends if t.impact == "positive"]
            if positive_trends:
                summary_parts.append("• Consider capitalizing on positive market momentum")
            
            negative_trends = [t for t in trends if t.impact == "negative"]
            if negative_trends:
                summary_parts.append("• Develop risk mitigation strategies for identified concerns")
        
        summary_parts.append("• Continue monitoring market conditions for emerging opportunities")
        
        # Footer
        summary_parts.append("")
        summary_parts.append(f"Analysis completed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_parts.append("Data sources: " + ", ".join(set(data.source for data in market_data)))
        
        full_summary = "\n".join(summary_parts)
        return self._truncate_summary(full_summary)
    
    async def test_connection(self) -> bool:
        """Test OpenAI API connection."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False
