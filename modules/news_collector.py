"""
News collection module for gathering cryptocurrency news from various sources.
This implementation provides both WebSocket and REST API news collection.
"""

import json
import time
import threading
import urllib.request
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from urllib.parse import urlencode

from config import config
from simple_storage import data_store
from utils.logging import get_logger
from exceptions import NewsCollectionError

logger = get_logger(__name__)


class NewsItem:
    """News item data structure."""
    
    def __init__(
        self,
        title: str,
        content: str = "",
        source: str = "",
        platform: str = "",
        url: str = "",
        published_at: Optional[datetime] = None
    ):
        self.title = title
        self.content = content
        self.source = source
        self.platform = platform
        self.url = url
        self.published_at = published_at or datetime.utcnow()
        self.received_at = datetime.utcnow()
        
        # Will be filled by sentiment analysis
        self.sentiment = "neutral"
        self.sentiment_score = 0.0
        self.confidence = 0.0
        self.mentioned_coins = []
        self.keywords_matched = []
        
        # Processing flags
        self.processed = False
        self.triggered_trade = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'title': self.title,
            'content': self.content,
            'source': self.source,
            'platform': self.platform,
            'url': self.url,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'received_at': self.received_at.isoformat(),
            'sentiment': self.sentiment,
            'sentiment_score': self.sentiment_score,
            'confidence': self.confidence,
            'mentioned_coins': json.dumps(self.mentioned_coins),
            'keywords_matched': json.dumps(self.keywords_matched),
            'processed': self.processed,
            'triggered_trade': self.triggered_trade
        }


class NewsCollector:
    """Base class for news collectors."""
    
    def __init__(self):
        self.running = False
        self.callbacks: List[Callable[[NewsItem], None]] = []
        self.error_callbacks: List[Callable[[Exception], None]] = []
    
    def add_callback(self, callback: Callable[[NewsItem], None]):
        """Add callback for new news items."""
        self.callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[Exception], None]):
        """Add callback for errors."""
        self.error_callbacks.append(callback)
    
    def _notify_callbacks(self, news_item: NewsItem):
        """Notify all callbacks of new news item."""
        for callback in self.callbacks:
            try:
                callback(news_item)
            except Exception as e:
                logger.error(f"Error in news callback: {e}")
    
    def _notify_error_callbacks(self, error: Exception):
        """Notify all error callbacks."""
        for callback in self.error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
    
    def start(self):
        """Start collecting news."""
        raise NotImplementedError
    
    def stop(self):
        """Stop collecting news."""
        self.running = False


class MockNewsCollector(NewsCollector):
    """Mock news collector for testing and development."""
    
    def __init__(self, interval: int = 30):
        super().__init__()
        self.interval = interval
        self.thread = None
        self.news_templates = [
            {
                "title": "Bitcoin reaches new all-time high amid institutional adoption",
                "content": "Bitcoin has surged to unprecedented levels as major corporations announce crypto adoption strategies.",
                "source": "CryptoNews",
                "platform": "Mock",
                "sentiment_hint": "positive",
                "coins": ["BTC"]
            },
            {
                "title": "Ethereum network upgrade completed successfully",
                "content": "The latest Ethereum upgrade has been deployed, bringing improved scalability and reduced fees.",
                "source": "ETH Foundation",
                "platform": "Mock",
                "sentiment_hint": "positive",
                "coins": ["ETH"]
            },
            {
                "title": "Regulatory concerns impact crypto market sentiment",
                "content": "New regulatory proposals have raised concerns among cryptocurrency investors.",
                "source": "Financial Times",
                "platform": "Mock",
                "sentiment_hint": "negative",
                "coins": ["BTC", "ETH"]
            },
            {
                "title": "Major exchange reports security breach",
                "content": "A popular cryptocurrency exchange has temporarily halted trading due to security concerns.",
                "source": "Security Alert",
                "platform": "Mock",
                "sentiment_hint": "negative",
                "coins": ["BTC", "ETH", "BNB"]
            },
            {
                "title": "DeFi protocol launches new staking rewards",
                "content": "A leading decentralized finance protocol has announced enhanced staking rewards for token holders.",
                "source": "DeFi Pulse",
                "platform": "Mock",
                "sentiment_hint": "positive",
                "coins": ["ETH", "ADA"]
            }
        ]
        self.current_index = 0
    
    def start(self):
        """Start the mock news collector."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.thread.start()
        logger.info("Mock news collector started")
    
    def stop(self):
        """Stop the mock news collector."""
        super().stop()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Mock news collector stopped")
    
    def _collect_loop(self):
        """Main collection loop."""
        while self.running:
            try:
                # Generate mock news
                template = self.news_templates[self.current_index % len(self.news_templates)]
                
                news_item = NewsItem(
                    title=template["title"],
                    content=template["content"],
                    source=template["source"],
                    platform=template["platform"],
                    published_at=datetime.utcnow()
                )
                
                # Add some mock metadata
                news_item.mentioned_coins = template.get("coins", [])
                
                logger.info(f"Generated mock news: {news_item.title}")
                self._notify_callbacks(news_item)
                
                self.current_index += 1
                
                # Wait for next iteration
                for _ in range(self.interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in mock news collection: {e}")
                self._notify_error_callbacks(e)
                time.sleep(5)


class RestNewsCollector(NewsCollector):
    """REST API-based news collector for demonstration."""
    
    def __init__(self, interval: int = 60):
        super().__init__()
        self.interval = interval
        self.thread = None
        
        # Mock REST endpoints (in real implementation, these would be actual news APIs)
        self.endpoints = [
            {
                "name": "CoinDesk",
                "url": "https://api.coindesk.com/v1/news/articles",  # Mock URL
                "parser": self._parse_coindesk_response
            },
            {
                "name": "CryptoNews",
                "url": "https://api.cryptonews.net/latest",  # Mock URL  
                "parser": self._parse_crypto_news_response
            }
        ]
    
    def start(self):
        """Start the REST news collector."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.thread.start()
        logger.info("REST news collector started")
    
    def stop(self):
        """Stop the REST news collector."""
        super().stop()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("REST news collector stopped")
    
    def _collect_loop(self):
        """Main collection loop."""
        while self.running:
            try:
                for endpoint in self.endpoints:
                    if not self.running:
                        break
                    
                    try:
                        self._fetch_from_endpoint(endpoint)
                    except Exception as e:
                        logger.error(f"Error fetching from {endpoint['name']}: {e}")
                
                # Wait for next iteration
                for _ in range(self.interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in REST news collection: {e}")
                self._notify_error_callbacks(e)
                time.sleep(10)
    
    def _fetch_from_endpoint(self, endpoint: Dict[str, Any]):
        """Fetch news from a single endpoint."""
        try:
            # In a real implementation, this would make actual HTTP requests
            # For now, we'll simulate with mock data
            logger.debug(f"Simulating fetch from {endpoint['name']}")
            
            # Simulate API response delay
            time.sleep(0.5)
            
            # Generate mock response
            mock_response = {
                "articles": [
                    {
                        "title": f"Latest crypto news from {endpoint['name']}",
                        "content": "Mock news content for testing purposes",
                        "published_at": datetime.utcnow().isoformat(),
                        "url": f"https://{endpoint['name'].lower()}.com/article/123"
                    }
                ]
            }
            
            # Parse response
            news_items = endpoint['parser'](mock_response)
            for news_item in news_items:
                self._notify_callbacks(news_item)
                
        except Exception as e:
            logger.error(f"Error in _fetch_from_endpoint: {e}")
            raise NewsCollectionError(f"Failed to fetch from {endpoint['name']}: {e}")
    
    def _parse_coindesk_response(self, response: Dict[str, Any]) -> List[NewsItem]:
        """Parse CoinDesk API response."""
        news_items = []
        for article in response.get('articles', []):
            news_item = NewsItem(
                title=article.get('title', ''),
                content=article.get('content', ''),
                source="CoinDesk",
                platform="REST_API",
                url=article.get('url', ''),
                published_at=datetime.fromisoformat(article.get('published_at', '').replace('Z', '+00:00')) if article.get('published_at') else None
            )
            news_items.append(news_item)
        return news_items
    
    def _parse_crypto_news_response(self, response: Dict[str, Any]) -> List[NewsItem]:
        """Parse CryptoNews API response."""
        news_items = []
        for article in response.get('articles', []):
            news_item = NewsItem(
                title=article.get('title', ''),
                content=article.get('content', ''),
                source="CryptoNews",
                platform="REST_API",
                url=article.get('url', ''),
                published_at=datetime.fromisoformat(article.get('published_at', '').replace('Z', '+00:00')) if article.get('published_at') else None
            )
            news_items.append(news_item)
        return news_items


class NewsCollectionManager:
    """Manages multiple news collectors and coordinates collection."""
    
    def __init__(self):
        self.collectors: List[NewsCollector] = []
        self.running = False
        self.news_handlers: List[Callable[[NewsItem], None]] = []
    
    def add_collector(self, collector: NewsCollector):
        """Add a news collector."""
        collector.add_callback(self._handle_news_item)
        collector.add_error_callback(self._handle_error)
        self.collectors.append(collector)
        logger.info(f"Added collector: {collector.__class__.__name__}")
    
    def add_news_handler(self, handler: Callable[[NewsItem], None]):
        """Add handler for collected news items."""
        self.news_handlers.append(handler)
    
    def start(self):
        """Start all collectors."""
        if self.running:
            return
        
        self.running = True
        for collector in self.collectors:
            collector.start()
        
        logger.info(f"Started {len(self.collectors)} news collectors")
    
    def stop(self):
        """Stop all collectors."""
        self.running = False
        for collector in self.collectors:
            collector.stop()
        
        logger.info("Stopped all news collectors")
    
    def _handle_news_item(self, news_item: NewsItem):
        """Handle incoming news item."""
        try:
            # Save to storage
            news_id = data_store.save_news_item(news_item.to_dict())
            logger.info(f"Collected news: {news_item.title} (ID: {news_id})")
            
            # Notify handlers
            for handler in self.news_handlers:
                try:
                    handler(news_item)
                except Exception as e:
                    logger.error(f"Error in news handler: {e}")
                    
        except Exception as e:
            logger.error(f"Error handling news item: {e}")
    
    def _handle_error(self, error: Exception):
        """Handle collector errors."""
        logger.error(f"News collection error: {error}")


# Create default news collection manager
news_manager = NewsCollectionManager()

# Add default collectors
news_manager.add_collector(MockNewsCollector(interval=30))  # Generate news every 30 seconds

if config.environment == "production":
    # In production, add real collectors
    news_manager.add_collector(RestNewsCollector(interval=60))


def start_news_collection():
    """Start news collection."""
    news_manager.start()


def stop_news_collection():
    """Stop news collection."""
    news_manager.stop()


def add_news_handler(handler: Callable[[NewsItem], None]):
    """Add handler for new news items."""
    news_manager.add_news_handler(handler)