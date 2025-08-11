"""
Configuration management for the crypto trading system.
Supports environment variables and configuration files.
"""

import os
import json
from typing import List, Dict, Any, Optional


class TradingConfig:
    """Main configuration class for the trading system."""
    
    def __init__(self):
        # Environment settings
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        
        # Binance API settings
        self.binance_api_key = os.getenv("BINANCE_API_KEY", "")
        self.binance_api_secret = os.getenv("BINANCE_API_SECRET", "")
        self.binance_testnet = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
        
        # News WebSocket settings
        self.news_websocket_url = os.getenv(
            "NEWS_WEBSOCKET_URL",
            "wss://api.formula-news.com/ws"
        )
        
        # Trading parameters
        self.stop_loss_percentage = float(os.getenv("STOP_LOSS_PERCENTAGE", "0.1"))
        self.trade_amount_usdt = float(os.getenv("TRADE_AMOUNT_USDT", "10.0"))
        
        # Trading pairs and amounts
        self.supported_coins = self._get_list_env("SUPPORTED_COINS", 
            ["BTC", "ETH", "BNB", "ADA", "SOL"])
        
        self.trade_amounts = self._get_dict_env("TRADE_AMOUNTS", {
            "BTCUSDT": 10.0,
            "ETHUSDT": 10.0,
            "BNBUSDT": 10.0,
            "ADAUSDT": 10.0,
            "SOLUSDT": 10.0
        })
        
        # Sentiment analysis keywords
        self.positive_keywords = self._get_list_env("POSITIVE_KEYWORDS", [
            "bullish", "moon", "pump", "rally", "partnership", "adoption",
            "breakthrough", "upgrade", "integration", "listing", "launch",
            "回购", "合作", "上线", "奖励", "质押", "利好", "上涨", "突破"
        ])
        
        self.negative_keywords = self._get_list_env("NEGATIVE_KEYWORDS", [
            "bearish", "dump", "crash", "hack", "scam", "regulation", "ban",
            "lawsuit", "shutdown", "bankruptcy", "exploit", "vulnerability",
            "被盗", "崩盘", "黑客", "破产", "停运", "利空", "下跌", "暴跌"
        ])
        
        # News filtering settings
        self.focus_platforms = self._get_list_env("FOCUS_PLATFORMS",
            ["Binance", "CoinDesk", "CoinTelegraph", "Bloomberg"])
        
        self.focus_keywords = self._get_list_env("FOCUS_KEYWORDS",
            ["Bitcoin", "Ethereum", "BTC", "ETH", "crypto", "cryptocurrency"])
        
        # Database settings
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./crypto_trading.db")
        
        # API settings
        self.api_host = os.getenv("API_HOST", "127.0.0.1")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        
        # Logging settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "crypto_trading.log")
        
        # Risk management
        self.max_open_positions = int(os.getenv("MAX_OPEN_POSITIONS", "5"))
        self.max_daily_trades = int(os.getenv("MAX_DAILY_TRADES", "20"))
        self.daily_loss_limit = float(os.getenv("DAILY_LOSS_LIMIT", "100.0"))
    
    def _get_list_env(self, key: str, default: List[str]) -> List[str]:
        """Get list value from environment variable."""
        value = os.getenv(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value.split(",")
        return default
    
    def _get_dict_env(self, key: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """Get dictionary value from environment variable."""
        value = os.getenv(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        return default
    
    def get_trade_symbol(self, coin: str) -> str:
        """Convert coin symbol to trading pair (e.g., BTC -> BTCUSDT)."""
        if coin.upper().endswith("USDT"):
            return coin.upper()
        return f"{coin.upper()}USDT"
    
    def is_coin_supported(self, coin: str) -> bool:
        """Check if a coin is supported for trading."""
        return coin.upper() in [c.upper() for c in self.supported_coins]


# Global configuration instance
config = TradingConfig()