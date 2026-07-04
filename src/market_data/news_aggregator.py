"""
News Aggregator & Sentiment Analyzer
Scrapes Reuters, CNBC, WSJ, CNN for market-moving news
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import aiohttp
import pandas as pd
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class NewsSource(Enum):
    REUTERS = 'reuters'
    CNBC = 'cnbc'
    WSJ = 'wsj'
    CNN = 'cnn'
    BLOOMBERG = 'bloomberg'


class SentimentLevel(Enum):
    VERY_NEGATIVE = -2
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1
    VERY_POSITIVE = 2


@dataclass
class NewsArticle:
    """News article with sentiment"""
    title: str
    summary: str
    source: NewsSource
    timestamp: datetime
    url: str
    sentiment_score: float  # -1.0 to 1.0
    impact_level: str  # 'high', 'medium', 'low'
    related_symbols: List[str]  # ['ES', 'SPY', 'NVDA', etc.]
    relevance_score: float  # 0-1


class NewsAggregator:
    """
    Aggregates news from multiple sources and scores impact
    """
    
    MARKET_KEYWORDS = [
        'Fed', 'interest rates', 'inflation', 'earnings', 'guidance',
        'GDP', 'employment', 'NFP', 'inflation', 'CPI', 'PPI',
        'stock market', 'decline', 'rally', 'crash', 'correction',
        'recession', 'bull market', 'bear market', 'volatility'
    ]
    
    def __init__(self):
        self.news_cache: List[NewsArticle] = []
        self.last_fetch: Optional[datetime] = None
    
    async def fetch_latest_news(self, hours_back: int = 24, 
                               sources: List[NewsSource] = None) -> List[NewsArticle]:
        """
        Fetch latest news from specified sources
        
        Args:
            hours_back: Fetch news from last N hours
            sources: News sources to fetch from
        
        Returns:
            List of NewsArticle objects
        """
        if sources is None:
            sources = list(NewsSource)
        
        articles = []
        
        try:
            # In production, use NewsAPI, MediaStack, or direct scraping
            async with aiohttp.ClientSession() as session:
                for source in sources:
                    try:
                        source_articles = await self._fetch_from_source(session, source, hours_back)
                        articles.extend(source_articles)
                    except Exception as e:
                        logger.error(f"Error fetching from {source.value}: {e}")
            
            # Score sentiment and relevance
            for article in articles:
                article.sentiment_score = self._score_sentiment(article.title + " " + article.summary)
                article.impact_level = self._determine_impact_level(article.title, article.sentiment_score)
                article.related_symbols = self._extract_symbols(article.title + " " + article.summary)
                article.relevance_score = self._calculate_relevance(article)
            
            # Sort by relevance and recency
            articles.sort(key=lambda x: (x.relevance_score, x.impact_level == 'high'), reverse=True)
            
            self.news_cache = articles[:100]  # Keep top 100
            self.last_fetch = datetime.now()
            
            logger.info(f"Fetched {len(articles)} news articles")
            return articles
        
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return []
    
    async def _fetch_from_source(self, session: aiohttp.ClientSession, 
                                 source: NewsSource, hours_back: int) -> List[NewsArticle]:
        """
        Fetch news from specific source
        Placeholder for actual API calls
        """
        articles = []
        
        try:
            # TODO: Implement actual API calls to NewsAPI, MediaStack, etc.
            # This is a placeholder
            
            logger.debug(f"Fetched from {source.value}")
        except Exception as e:
            logger.error(f"Error fetching from {source.value}: {e}")
        
        return articles
    
    def _score_sentiment(self, text: str) -> float:
        """
        Score sentiment of text (-1.0 to 1.0)
        Uses simple keyword matching
        """
        try:
            # In production, use transformers library for accurate sentiment
            # from transformers import pipeline
            # sentiment_pipeline = pipeline('sentiment-analysis', 
            #     model='distilbert-base-uncased-finetuned-sst-2-english')
            
            positive_words = ['rally', 'surge', 'soar', 'beat', 'strong', 'outperform', 
                            'gain', 'profit', 'growth', 'bull']
            negative_words = ['crash', 'plunge', 'decline', 'miss', 'weak', 'underperform',
                            'loss', 'bear', 'recession', 'downturn']
            
            text_lower = text.lower()
            
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count + negative_count == 0:
                return 0.0
            
            sentiment = (positive_count - negative_count) / (positive_count + negative_count)
            return min(1.0, max(-1.0, sentiment))
        
        except Exception as e:
            logger.error(f"Error scoring sentiment: {e}")
            return 0.0
    
    def _determine_impact_level(self, title: str, sentiment_score: float) -> str:
        """
        Determine impact level based on keywords and sentiment
        """
        high_impact_keywords = ['Fed', 'FOMC', 'rate hike', 'rate cut', 'earnings beat', 
                               'earnings miss', 'crash', 'circuit breaker']
        
        title_lower = title.lower()
        
        if any(keyword.lower() in title_lower for keyword in high_impact_keywords):
            return 'high'
        elif abs(sentiment_score) > 0.7:
            return 'high'
        elif abs(sentiment_score) > 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _extract_symbols(self, text: str) -> List[str]:
        """
        Extract ticker symbols from text
        """
        symbols = []
        
        # Simple pattern matching for stock tickers
        mag7 = ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
        indices = ['ES', 'SPY', 'IWM', 'DIA', 'QQQ']
        all_tickers = mag7 + indices
        
        for ticker in all_tickers:
            if ticker in text.upper():
                symbols.append(ticker)
        
        return list(set(symbols))  # Remove duplicates
    
    def _calculate_relevance(self, article: NewsArticle) -> float:
        """
        Calculate relevance score for market trading (0-1)
        """
        relevance = 0.0
        
        # Impact level weight
        impact_weights = {'high': 0.5, 'medium': 0.3, 'low': 0.1}
        relevance += impact_weights.get(article.impact_level, 0.1)
        
        # Sentiment extremeness
        relevance += 0.2 * abs(article.sentiment_score)
        
        # Symbol relevance (ES/SPY more relevant than single stocks)
        if 'ES' in article.related_symbols or 'SPY' in article.related_symbols:
            relevance += 0.3
        elif len(article.related_symbols) > 0:
            relevance += 0.1
        
        return min(1.0, relevance)
    
    def get_sentiment_summary(self, lookback_hours: int = 24) -> Dict:
        """
        Get overall sentiment summary
        """
        try:
            if not self.news_cache:
                return {'overall_sentiment': 0, 'bullish_count': 0, 'bearish_count': 0}
            
            # Filter by time
            now = datetime.now()
            recent_articles = [
                a for a in self.news_cache 
                if (now - a.timestamp).total_seconds() < lookback_hours * 3600
            ]
            
            if not recent_articles:
                return {'overall_sentiment': 0, 'bullish_count': 0, 'bearish_count': 0}
            
            avg_sentiment = sum(a.sentiment_score for a in recent_articles) / len(recent_articles)
            bullish_count = sum(1 for a in recent_articles if a.sentiment_score > 0.3)
            bearish_count = sum(1 for a in recent_articles if a.sentiment_score < -0.3)
            
            return {
                'overall_sentiment': float(avg_sentiment),
                'bullish_count': bullish_count,
                'bearish_count': bearish_count,
                'neutral_count': len(recent_articles) - bullish_count - bearish_count
            }
        
        except Exception as e:
            logger.error(f"Error getting sentiment summary: {e}")
            return {}
