"""
Sentiment analysis module for cryptocurrency news.
Implements both keyword-based and simple NLP sentiment analysis.
"""

import re
import json
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

from config import config
from simple_storage import data_store
from utils.logging import get_logger
from exceptions import SentimentAnalysisError

logger = get_logger(__name__)


class SentimentResult:
    """Sentiment analysis result."""
    
    def __init__(
        self,
        sentiment: str,
        score: float,
        confidence: float,
        mentioned_coins: List[str],
        keywords_matched: List[str],
        method: str = "keyword"
    ):
        self.sentiment = sentiment  # 'positive', 'negative', 'neutral'
        self.score = score  # -1.0 to 1.0
        self.confidence = confidence  # 0.0 to 1.0
        self.mentioned_coins = mentioned_coins
        self.keywords_matched = keywords_matched
        self.method = method


class KeywordSentimentAnalyzer:
    """Keyword-based sentiment analysis."""
    
    def __init__(self):
        self.positive_keywords = config.positive_keywords
        self.negative_keywords = config.negative_keywords
        
        # Coin patterns for detection
        self.coin_patterns = self._build_coin_patterns()
    
    def _build_coin_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for coin detection."""
        patterns = {}
        
        # Common cryptocurrency symbols and names
        crypto_mapping = {
            'BTC': ['bitcoin', 'btc', 'btc/usd', 'btcusdt'],
            'ETH': ['ethereum', 'eth', 'eth/usd', 'ethusdt', 'ether'],
            'BNB': ['binance coin', 'bnb', 'bnb/usd', 'bnbusdt'],
            'ADA': ['cardano', 'ada', 'ada/usd', 'adausdt'],
            'SOL': ['solana', 'sol', 'sol/usd', 'solusdt'],
            'XRP': ['ripple', 'xrp', 'xrp/usd', 'xrpusdt'],
            'DOT': ['polkadot', 'dot', 'dot/usd', 'dotusdt'],
            'LINK': ['chainlink', 'link', 'link/usd', 'linkusdt'],
            'MATIC': ['polygon', 'matic', 'matic/usd', 'maticusdt'],
            'AVAX': ['avalanche', 'avax', 'avax/usd', 'avaxusdt']
        }
        
        for coin, variations in crypto_mapping.items():
            patterns[coin] = [
                rf'\b{re.escape(variant)}\b' 
                for variant in variations
            ]
        
        return patterns
    
    def analyze(self, text: str, title: str = "") -> SentimentResult:
        """Analyze sentiment of text."""
        try:
            # Combine title and content for analysis
            full_text = f"{title} {text}".lower()
            
            # Find mentioned coins
            mentioned_coins = self._extract_coins(full_text)
            
            # Find matched keywords
            positive_matches = self._find_keyword_matches(full_text, self.positive_keywords)
            negative_matches = self._find_keyword_matches(full_text, self.negative_keywords)
            
            # Calculate sentiment
            sentiment, score, confidence = self._calculate_sentiment(
                positive_matches, negative_matches, full_text
            )
            
            all_matches = positive_matches + negative_matches
            
            return SentimentResult(
                sentiment=sentiment,
                score=score,
                confidence=confidence,
                mentioned_coins=mentioned_coins,
                keywords_matched=all_matches,
                method="keyword"
            )
            
        except Exception as e:
            logger.error(f"Error in keyword sentiment analysis: {e}")
            raise SentimentAnalysisError(f"Keyword analysis failed: {e}")
    
    def _extract_coins(self, text: str) -> List[str]:
        """Extract mentioned cryptocurrency symbols from text."""
        mentioned_coins = []
        
        for coin, patterns in self.coin_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    if coin not in mentioned_coins:
                        mentioned_coins.append(coin)
                    break
        
        return mentioned_coins
    
    def _find_keyword_matches(self, text: str, keywords: List[str]) -> List[str]:
        """Find keyword matches in text."""
        matches = []
        
        for keyword in keywords:
            # Create word boundary pattern for better matching
            pattern = rf'\b{re.escape(keyword.lower())}\b'
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(keyword)
        
        return matches
    
    def _calculate_sentiment(
        self, 
        positive_matches: List[str], 
        negative_matches: List[str],
        text: str
    ) -> Tuple[str, float, float]:
        """Calculate sentiment score and confidence."""
        pos_count = len(positive_matches)
        neg_count = len(negative_matches)
        
        # Simple scoring algorithm
        if pos_count == 0 and neg_count == 0:
            return "neutral", 0.0, 0.1
        
        # Calculate raw score
        total_matches = pos_count + neg_count
        pos_ratio = pos_count / total_matches if total_matches > 0 else 0
        neg_ratio = neg_count / total_matches if total_matches > 0 else 0
        
        # Score between -1 and 1
        score = pos_ratio - neg_ratio
        
        # Determine sentiment category
        if score > 0.2:
            sentiment = "positive"
        elif score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Calculate confidence based on number of matches and text length
        text_length = len(text.split())
        match_density = total_matches / max(text_length, 1)
        
        # Confidence increases with more matches and higher match density
        confidence = min(0.9, 0.3 + (total_matches * 0.1) + (match_density * 0.4))
        
        return sentiment, score, confidence


class SimpleLexiconAnalyzer:
    """Simple lexicon-based sentiment analyzer as backup."""
    
    def __init__(self):
        # Simple sentiment lexicon
        self.sentiment_words = {
            'positive': [
                'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
                'bullish', 'up', 'rise', 'gain', 'profit', 'success', 'win',
                'strong', 'high', 'boost', 'surge', 'rally', 'moon'
            ],
            'negative': [
                'bad', 'terrible', 'awful', 'horrible', 'disappointing', 'fail',
                'bearish', 'down', 'fall', 'drop', 'loss', 'crash', 'dump',
                'weak', 'low', 'decline', 'plunge', 'collapse', 'bear'
            ]
        }
    
    def analyze(self, text: str, title: str = "") -> SentimentResult:
        """Simple lexicon-based sentiment analysis."""
        try:
            full_text = f"{title} {text}".lower()
            words = re.findall(r'\b\w+\b', full_text)
            
            pos_count = sum(1 for word in words if word in self.sentiment_words['positive'])
            neg_count = sum(1 for word in words if word in self.sentiment_words['negative'])
            
            total_sentiment_words = pos_count + neg_count
            
            if total_sentiment_words == 0:
                sentiment = "neutral"
                score = 0.0
                confidence = 0.1
            else:
                score = (pos_count - neg_count) / len(words)
                
                if score > 0.01:
                    sentiment = "positive"
                elif score < -0.01:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
                
                confidence = min(0.7, total_sentiment_words / len(words) * 2)
            
            # Extract coins using simple pattern matching
            mentioned_coins = []
            for coin in config.supported_coins:
                if coin.lower() in full_text:
                    mentioned_coins.append(coin)
            
            matched_words = [word for word in words 
                           if word in self.sentiment_words['positive'] 
                           or word in self.sentiment_words['negative']]
            
            return SentimentResult(
                sentiment=sentiment,
                score=score,
                confidence=confidence,
                mentioned_coins=mentioned_coins,
                keywords_matched=matched_words,
                method="lexicon"
            )
            
        except Exception as e:
            logger.error(f"Error in lexicon sentiment analysis: {e}")
            raise SentimentAnalysisError(f"Lexicon analysis failed: {e}")


class SentimentAnalyzer:
    """Main sentiment analyzer that combines multiple methods."""
    
    def __init__(self):
        self.keyword_analyzer = KeywordSentimentAnalyzer()
        self.lexicon_analyzer = SimpleLexiconAnalyzer()
    
    def analyze(self, text: str, title: str = "") -> SentimentResult:
        """Analyze sentiment using the best available method."""
        try:
            # Primary analysis using keyword method
            keyword_result = self.keyword_analyzer.analyze(text, title)
            
            # If confidence is low, try lexicon method and combine
            if keyword_result.confidence < 0.5:
                lexicon_result = self.lexicon_analyzer.analyze(text, title)
                
                # Combine results (weighted average)
                combined_score = (
                    keyword_result.score * keyword_result.confidence +
                    lexicon_result.score * lexicon_result.confidence
                ) / (keyword_result.confidence + lexicon_result.confidence)
                
                combined_confidence = min(0.9, 
                    (keyword_result.confidence + lexicon_result.confidence) / 2)
                
                # Determine final sentiment
                if combined_score > 0.1:
                    sentiment = "positive"
                elif combined_score < -0.1:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
                
                # Combine mentioned coins and keywords
                mentioned_coins = list(set(
                    keyword_result.mentioned_coins + lexicon_result.mentioned_coins
                ))
                keywords_matched = list(set(
                    keyword_result.keywords_matched + lexicon_result.keywords_matched
                ))
                
                return SentimentResult(
                    sentiment=sentiment,
                    score=combined_score,
                    confidence=combined_confidence,
                    mentioned_coins=mentioned_coins,
                    keywords_matched=keywords_matched,
                    method="combined"
                )
            
            return keyword_result
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            # Return neutral sentiment as fallback
            return SentimentResult(
                sentiment="neutral",
                score=0.0,
                confidence=0.1,
                mentioned_coins=[],
                keywords_matched=[],
                method="fallback"
            )
    
    def analyze_news_item(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of a news item and update its data."""
        try:
            title = news_data.get('title', '')
            content = news_data.get('content', '')
            
            # Perform sentiment analysis
            result = self.analyze(content, title)
            
            # Update news data with sentiment results
            news_data.update({
                'sentiment': result.sentiment,
                'sentiment_score': result.score,
                'confidence': result.confidence,
                'mentioned_coins': json.dumps(result.mentioned_coins),
                'keywords_matched': json.dumps(result.keywords_matched),
                'processed': True
            })
            
            logger.info(
                f"Analyzed sentiment: {result.sentiment} "
                f"(score: {result.score:.2f}, confidence: {result.confidence:.2f}) "
                f"for news: {title[:50]}..."
            )
            
            return news_data
            
        except Exception as e:
            logger.error(f"Error analyzing news item sentiment: {e}")
            news_data.update({
                'sentiment': 'neutral',
                'sentiment_score': 0.0,
                'confidence': 0.1,
                'mentioned_coins': json.dumps([]),
                'keywords_matched': json.dumps([]),
                'processed': True
            })
            return news_data


class SentimentProcessor:
    """Processes news items for sentiment analysis."""
    
    def __init__(self):
        self.analyzer = SentimentAnalyzer()
        self.running = False
    
    def process_pending_news(self):
        """Process all unprocessed news items."""
        try:
            # Get unprocessed news items
            all_news = data_store.get_news_items(limit=100)
            unprocessed = [news for news in all_news if not news.get('processed', False)]
            
            logger.info(f"Processing {len(unprocessed)} unprocessed news items")
            
            for news_data in unprocessed:
                try:
                    # Analyze sentiment
                    updated_data = self.analyzer.analyze_news_item(news_data)
                    
                    # Update in storage
                    data_store.update_news_item(news_data['id'], updated_data)
                    
                except Exception as e:
                    logger.error(f"Error processing news item {news_data.get('id')}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in process_pending_news: {e}")
    
    def process_news_item(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single news item."""
        return self.analyzer.analyze_news_item(news_data)


# Global sentiment processor
sentiment_processor = SentimentProcessor()


def analyze_sentiment(text: str, title: str = "") -> SentimentResult:
    """Analyze sentiment of text."""
    analyzer = SentimentAnalyzer()
    return analyzer.analyze(text, title)


def process_news_sentiment(news_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process sentiment for a news item."""
    return sentiment_processor.process_news_item(news_data)


def process_all_pending_sentiment():
    """Process sentiment for all pending news items."""
    sentiment_processor.process_pending_news()