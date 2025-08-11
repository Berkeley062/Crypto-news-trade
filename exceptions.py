"""Custom exceptions for the crypto trading system."""

from typing import Optional, Any, Dict


class CryptoTradingException(Exception):
    """Base exception for crypto trading system."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(CryptoTradingException):
    """Raised when there's a configuration error."""
    pass


class NewsCollectionError(CryptoTradingException):
    """Raised when news collection fails."""
    pass


class SentimentAnalysisError(CryptoTradingException):
    """Raised when sentiment analysis fails."""
    pass


class TradingError(CryptoTradingException):
    """Raised when trading operations fail."""
    pass


class BinanceAPIError(TradingError):
    """Raised when Binance API operations fail."""
    pass


class PositionError(TradingError):
    """Raised when position management fails."""
    pass


class StopLossError(TradingError):
    """Raised when stop-loss operations fail."""
    pass


class DatabaseError(CryptoTradingException):
    """Raised when database operations fail."""
    pass


class ValidationError(CryptoTradingException):
    """Raised when data validation fails."""
    pass


class RiskManagementError(TradingError):
    """Raised when risk management checks fail."""
    pass


class APIError(CryptoTradingException):
    """Raised when API operations fail."""
    pass


class WebSocketError(CryptoTradingException):
    """Raised when WebSocket operations fail."""
    pass