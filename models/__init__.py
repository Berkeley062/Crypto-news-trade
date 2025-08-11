"""Database models for the crypto trading system."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class SentimentType(str, Enum):
    """News sentiment types."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class OrderSide(str, Enum):
    """Trading order sides."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """Trading order status."""
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    PENDING_CANCEL = "PENDING_CANCEL"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class PositionStatus(str, Enum):
    """Position status."""
    OPEN = "open"
    CLOSED = "closed"
    STOPPED = "stopped"  # Closed via stop-loss


class NewsItem(Base):
    """News item model."""
    
    __tablename__ = "news_items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    source = Column(String(100))
    platform = Column(String(100))
    url = Column(String(500))
    published_at = Column(DateTime)
    received_at = Column(DateTime, default=func.now())
    
    # Sentiment analysis results
    sentiment = Column(SQLEnum(SentimentType), default=SentimentType.NEUTRAL)
    sentiment_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    
    # Extracted information
    mentioned_coins = Column(String(200))  # JSON string of coin symbols
    keywords_matched = Column(String(500))  # JSON string of matched keywords
    
    # Processing flags
    processed = Column(Boolean, default=False)
    triggered_trade = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class TradingOrder(Base):
    """Trading order model."""
    
    __tablename__ = "trading_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    binance_order_id = Column(String(50), unique=True, index=True)
    symbol = Column(String(20), nullable=False)
    side = Column(SQLEnum(OrderSide), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float)
    
    # Order status and execution
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.NEW)
    executed_quantity = Column(Float, default=0.0)
    executed_price = Column(Float, default=0.0)
    
    # Related data
    news_item_id = Column(Integer)  # Foreign key to news item that triggered this
    position_id = Column(Integer)   # Foreign key to position
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    executed_at = Column(DateTime)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Position(Base):
    """Trading position model."""
    
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    
    # Position details
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, default=0.0)
    
    # P&L calculation
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    
    # Stop-loss settings
    stop_loss_price = Column(Float)
    stop_loss_percentage = Column(Float, default=0.1)
    
    # Status and flags
    status = Column(SQLEnum(PositionStatus), default=PositionStatus.OPEN)
    is_monitoring = Column(Boolean, default=True)
    
    # Related data
    entry_order_id = Column(Integer)  # Foreign key to entry order
    exit_order_id = Column(Integer)   # Foreign key to exit order
    news_item_id = Column(Integer)    # Foreign key to triggering news
    
    # Timestamps
    opened_at = Column(DateTime, default=func.now())
    closed_at = Column(DateTime)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SystemMetrics(Base):
    """System performance metrics."""
    
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=func.now())
    
    # Trading metrics
    total_trades = Column(Integer, default=0)
    successful_trades = Column(Integer, default=0)
    failed_trades = Column(Integer, default=0)
    
    # P&L metrics
    daily_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    
    # News processing metrics
    news_processed = Column(Integer, default=0)
    trades_triggered = Column(Integer, default=0)
    
    # System health
    uptime_seconds = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())


class ConfigItem(Base):
    """Dynamic configuration storage."""
    
    __tablename__ = "config_items"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(String(500))
    data_type = Column(String(20), default="string")  # string, int, float, bool, json
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())