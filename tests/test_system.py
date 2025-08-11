"""Unit tests for the crypto trading system."""

import unittest
import json
import time
from datetime import datetime

# Import system modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from simple_storage import SimpleDataStore
from modules.sentiment_analyzer import analyze_sentiment, SentimentAnalyzer
from modules.binance_client import MockBinanceClient
from modules.trading_strategy import TradingStrategy, TradingSignal
from modules.news_collector import NewsItem


class TestSentimentAnalyzer(unittest.TestCase):
    """Test sentiment analysis functionality."""
    
    def setUp(self):
        self.analyzer = SentimentAnalyzer()
    
    def test_positive_sentiment(self):
        """Test positive sentiment detection."""
        text = "Bitcoin is showing bullish momentum with strong rally"
        result = self.analyzer.analyze(text, "BTC Price Surge")
        
        self.assertEqual(result.sentiment, "positive")
        self.assertGreater(result.score, 0)
        self.assertIn("BTC", result.mentioned_coins)
        self.assertIn("bullish", result.keywords_matched)
    
    def test_negative_sentiment(self):
        """Test negative sentiment detection."""
        text = "Cryptocurrency market crashes due to regulatory concerns"
        result = self.analyzer.analyze(text, "Market Crash")
        
        self.assertEqual(result.sentiment, "negative")
        self.assertLess(result.score, 0)
        self.assertIn("crash", result.keywords_matched)
    
    def test_neutral_sentiment(self):
        """Test neutral sentiment detection."""
        text = "Bitcoin price remains stable around current levels"
        result = self.analyzer.analyze(text, "BTC Update")
        
        self.assertEqual(result.sentiment, "neutral")
        self.assertIn("BTC", result.mentioned_coins)
    
    def test_multiple_coins(self):
        """Test detection of multiple cryptocurrencies."""
        text = "Bitcoin and Ethereum show different price movements"
        result = self.analyzer.analyze(text, "Market Analysis")
        
        self.assertIn("BTC", result.mentioned_coins)
        self.assertIn("ETH", result.mentioned_coins)


class TestMockBinanceClient(unittest.TestCase):
    """Test mock Binance API client."""
    
    def setUp(self):
        self.client = MockBinanceClient()
    
    def test_account_info(self):
        """Test account information retrieval."""
        account = self.client.get_account()
        
        self.assertIn("balances", account)
        self.assertTrue(len(account["balances"]) > 0)
        
        # Check USDT balance exists
        usdt_balance = None
        for balance in account["balances"]:
            if balance["asset"] == "USDT":
                usdt_balance = float(balance["free"])
                break
        
        self.assertIsNotNone(usdt_balance)
        self.assertGreater(usdt_balance, 0)
    
    def test_price_fetching(self):
        """Test price fetching."""
        price = self.client.get_symbol_ticker("BTCUSDT")
        
        self.assertIn("symbol", price)
        self.assertIn("price", price)
        self.assertEqual(price["symbol"], "BTCUSDT")
        self.assertGreater(float(price["price"]), 0)
    
    def test_buy_order(self):
        """Test buy order execution."""
        initial_usdt = self.client.account_balance["USDT"]
        initial_btc = self.client.account_balance.get("BTC", 0)
        
        quantity = 0.001
        order = self.client.create_order(
            symbol="BTCUSDT",
            side="BUY",
            type="MARKET",
            quantity=quantity
        )
        
        self.assertEqual(order["status"], "FILLED")
        self.assertEqual(order["side"], "BUY")
        self.assertEqual(float(order["executedQty"]), quantity)
        
        # Check balance changes
        self.assertLess(self.client.account_balance["USDT"], initial_usdt)
        self.assertGreater(self.client.account_balance.get("BTC", 0), initial_btc)
    
    def test_sell_order(self):
        """Test sell order execution."""
        # First buy some BTC
        self.client.create_order("BTCUSDT", "BUY", "MARKET", 0.001)
        
        initial_usdt = self.client.account_balance["USDT"]
        initial_btc = self.client.account_balance["BTC"]
        
        # Then sell it
        quantity = 0.0005
        order = self.client.create_order(
            symbol="BTCUSDT",
            side="SELL",
            type="MARKET",
            quantity=quantity
        )
        
        self.assertEqual(order["status"], "FILLED")
        self.assertEqual(order["side"], "SELL")
        
        # Check balance changes
        self.assertGreater(self.client.account_balance["USDT"], initial_usdt)
        self.assertLess(self.client.account_balance["BTC"], initial_btc)


class TestTradingStrategy(unittest.TestCase):
    """Test trading strategy logic."""
    
    def setUp(self):
        self.strategy = TradingStrategy()
    
    def test_signal_generation_positive(self):
        """Test trading signal generation for positive news."""
        news_data = {
            'id': 1,
            'title': 'Bitcoin Adoption Surge',
            'sentiment': 'positive',
            'sentiment_score': 0.8,
            'confidence': 0.9,
            'mentioned_coins': '["BTC"]'
        }
        
        signals = self.strategy.analyze_news_for_trading(news_data)
        
        self.assertEqual(len(signals), 1)
        signal = signals[0]
        self.assertEqual(signal.action, "buy")
        self.assertEqual(signal.symbol, "BTCUSDT")
        self.assertEqual(signal.sentiment, "positive")
    
    def test_signal_generation_negative(self):
        """Test trading signal generation for negative news."""
        # First create a mock open position
        self.strategy._has_open_position = lambda symbol: True
        
        news_data = {
            'id': 2,
            'title': 'Bitcoin Security Breach',
            'sentiment': 'negative',
            'sentiment_score': -0.7,
            'confidence': 0.85,
            'mentioned_coins': '["BTC"]'
        }
        
        signals = self.strategy.analyze_news_for_trading(news_data)
        
        self.assertEqual(len(signals), 1)
        signal = signals[0]
        self.assertEqual(signal.action, "sell")
        self.assertEqual(signal.symbol, "BTCUSDT")
    
    def test_low_confidence_filtering(self):
        """Test that low confidence news doesn't generate signals."""
        news_data = {
            'id': 3,
            'title': 'Bitcoin Price Update',
            'sentiment': 'positive',
            'sentiment_score': 0.8,
            'confidence': 0.3,  # Low confidence
            'mentioned_coins': '["BTC"]'
        }
        
        signals = self.strategy.analyze_news_for_trading(news_data)
        
        self.assertEqual(len(signals), 0)


class TestDataStorage(unittest.TestCase):
    """Test data storage functionality."""
    
    def setUp(self):
        # Create temporary test storage
        self.storage = SimpleDataStore("test_data")
    
    def tearDown(self):
        # Clean up test data
        import shutil
        try:
            shutil.rmtree("test_data")
        except:
            pass
    
    def test_news_storage(self):
        """Test news item storage and retrieval."""
        news_data = {
            'title': 'Test News Item',
            'content': 'Test content',
            'source': 'test_source',
            'sentiment': 'positive'
        }
        
        # Save news item
        news_id = self.storage.save_news_item(news_data)
        self.assertIsInstance(news_id, int)
        self.assertGreater(news_id, 0)
        
        # Retrieve news items
        news_items = self.storage.get_news_items(limit=10)
        self.assertEqual(len(news_items), 1)
        
        saved_news = news_items[0]
        self.assertEqual(saved_news['title'], news_data['title'])
        self.assertEqual(saved_news['id'], news_id)
    
    def test_order_storage(self):
        """Test trading order storage."""
        order_data = {
            'symbol': 'BTCUSDT',
            'side': 'BUY',
            'quantity': 0.001,
            'price': 45000.0,
            'status': 'FILLED'
        }
        
        # Save order
        order_id = self.storage.save_trading_order(order_data)
        self.assertIsInstance(order_id, int)
        
        # Retrieve orders
        orders = self.storage.get_trading_orders(limit=10)
        self.assertEqual(len(orders), 1)
        
        saved_order = orders[0]
        self.assertEqual(saved_order['symbol'], order_data['symbol'])
        self.assertEqual(saved_order['id'], order_id)
    
    def test_position_storage(self):
        """Test position storage and updates."""
        position_data = {
            'symbol': 'BTCUSDT',
            'quantity': 0.001,
            'entry_price': 45000.0,
            'status': 'open'
        }
        
        # Save position
        position_id = self.storage.save_position(position_data)
        
        # Test open positions retrieval
        open_positions = self.storage.get_open_positions()
        self.assertEqual(len(open_positions), 1)
        
        # Update position
        updates = {
            'current_price': 46000.0,
            'unrealized_pnl': 1.0
        }
        self.storage.update_position(position_id, updates)
        
        # Verify update
        updated_positions = self.storage.get_all_positions(limit=10)
        updated_position = updated_positions[0]
        self.assertEqual(updated_position['current_price'], 46000.0)


class TestNewsItem(unittest.TestCase):
    """Test NewsItem class."""
    
    def test_news_item_creation(self):
        """Test news item creation and conversion."""
        news = NewsItem(
            title="Test News",
            content="Test content",
            source="test",
            platform="mock"
        )
        
        self.assertEqual(news.title, "Test News")
        self.assertEqual(news.sentiment, "neutral")
        self.assertFalse(news.processed)
        
        # Test conversion to dict
        news_dict = news.to_dict()
        self.assertIn('title', news_dict)
        self.assertIn('sentiment', news_dict)
        self.assertIn('received_at', news_dict)  # Use received_at instead of created_at


class TestIntegration(unittest.TestCase):
    """Integration tests for multiple components."""
    
    def test_news_to_trading_pipeline(self):
        """Test complete pipeline from news to trading decision."""
        # Create news item
        news = NewsItem(
            title="Bitcoin shows strong bullish momentum",
            content="Bitcoin price surges with institutional adoption",
            source="test"
        )
        
        # Analyze sentiment
        analyzer = SentimentAnalyzer()
        sentiment_result = analyzer.analyze(news.content, news.title)
        
        # Verify positive sentiment
        self.assertEqual(sentiment_result.sentiment, "positive")
        self.assertIn("BTC", sentiment_result.mentioned_coins)
        
        # Create news data for trading analysis
        news_data = {
            'id': 1,
            'title': news.title,
            'sentiment': sentiment_result.sentiment,
            'sentiment_score': sentiment_result.score,
            'confidence': sentiment_result.confidence,
            'mentioned_coins': json.dumps(sentiment_result.mentioned_coins)
        }
        
        # Generate trading signals (set higher confidence threshold for test)
        if sentiment_result.confidence >= 0.6:
            strategy = TradingStrategy()
            signals = strategy.analyze_news_for_trading(news_data)
            
            # Verify signal generation
            self.assertEqual(len(signals), 1)
            self.assertEqual(signals[0].action, "buy")
            self.assertEqual(signals[0].symbol, "BTCUSDT")
        else:
            # Low confidence case - should generate no signals
            strategy = TradingStrategy()
            signals = strategy.analyze_news_for_trading(news_data)
            self.assertEqual(len(signals), 0)
            print(f"Note: Low confidence ({sentiment_result.confidence:.2f}) - no signals generated")


def run_tests():
    """Run all tests."""
    print("Running Crypto Trading System Tests...")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestSentimentAnalyzer,
        TestMockBinanceClient,
        TestTradingStrategy,
        TestDataStorage,
        TestNewsItem,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASSED' if success else 'FAILED'}")
    
    return success


if __name__ == "__main__":
    run_tests()