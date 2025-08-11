"""
Trading strategy module for executing trades based on news sentiment.
Implements automatic trading decisions and risk management.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from config import config
from simple_storage import data_store
from modules.binance_client import binance_api
from modules.sentiment_analyzer import SentimentResult
from utils.logging import get_logger
from exceptions import TradingError, RiskManagementError

logger = get_logger(__name__)


class TradingSignal:
    """Trading signal based on news sentiment."""
    
    def __init__(
        self,
        symbol: str,
        action: str,  # 'buy', 'sell', 'hold'
        confidence: float,
        sentiment: str,
        news_id: int,
        reasoning: str = "",
        quantity: Optional[float] = None
    ):
        self.symbol = symbol
        self.action = action
        self.confidence = confidence
        self.sentiment = sentiment
        self.news_id = news_id
        self.reasoning = reasoning
        self.quantity = quantity
        self.created_at = datetime.utcnow()


class RiskManager:
    """Risk management for trading operations."""
    
    def __init__(self):
        self.daily_trades = 0
        self.daily_loss = 0.0
        self.open_positions_count = 0
        self.last_reset = datetime.utcnow().date()
    
    def reset_daily_counters(self):
        """Reset daily counters if new day."""
        today = datetime.utcnow().date()
        if today > self.last_reset:
            self.daily_trades = 0
            self.daily_loss = 0.0
            self.last_reset = today
            logger.info("Reset daily risk management counters")
    
    def check_trade_limits(self, trade_amount: float) -> bool:
        """Check if trade is within risk limits."""
        self.reset_daily_counters()
        
        # Check daily trade limit
        if self.daily_trades >= config.max_daily_trades:
            logger.warning(f"Daily trade limit reached: {self.daily_trades}")
            return False
        
        # Check daily loss limit
        if self.daily_loss >= config.daily_loss_limit:
            logger.warning(f"Daily loss limit reached: {self.daily_loss:.2f}")
            return False
        
        # Check open positions limit
        open_positions = data_store.get_open_positions()
        if len(open_positions) >= config.max_open_positions:
            logger.warning(f"Maximum open positions limit reached: {len(open_positions)}")
            return False
        
        # Check account balance
        try:
            usdt_balance = binance_api.get_balance("USDT")
            if usdt_balance < trade_amount:
                logger.warning(f"Insufficient balance: {usdt_balance:.2f} < {trade_amount:.2f}")
                return False
        except Exception as e:
            logger.error(f"Error checking balance: {e}")
            return False
        
        return True
    
    def record_trade(self, pnl: float = 0.0):
        """Record a completed trade."""
        self.daily_trades += 1
        if pnl < 0:
            self.daily_loss += abs(pnl)
        logger.debug(f"Recorded trade: PnL={pnl:.2f}, Daily trades={self.daily_trades}")
    
    def can_open_position(self, symbol: str) -> bool:
        """Check if we can open a position for the symbol."""
        # Check if we already have an open position for this symbol
        open_positions = data_store.get_open_positions()
        for position in open_positions:
            if position.get("symbol") == symbol:
                logger.info(f"Already have open position for {symbol}")
                return False
        
        return True


class TradingStrategy:
    """Main trading strategy implementation."""
    
    def __init__(self):
        self.risk_manager = RiskManager()
        self.min_confidence = 0.6  # Minimum confidence to trigger trades
        self.sentiment_threshold = 0.3  # Minimum sentiment score
    
    def analyze_news_for_trading(self, news_data: Dict[str, Any]) -> List[TradingSignal]:
        """Analyze news item and generate trading signals."""
        signals = []
        
        try:
            # Extract sentiment data
            sentiment = news_data.get('sentiment', 'neutral')
            sentiment_score = news_data.get('sentiment_score', 0.0)
            confidence = news_data.get('confidence', 0.0)
            
            # Parse mentioned coins
            mentioned_coins_str = news_data.get('mentioned_coins', '[]')
            try:
                mentioned_coins = json.loads(mentioned_coins_str) if mentioned_coins_str else []
            except json.JSONDecodeError:
                mentioned_coins = []
            
            # Check if confidence is high enough
            if confidence < self.min_confidence:
                logger.debug(f"Confidence too low for trading: {confidence:.2f}")
                return signals
            
            # Generate signals for each mentioned coin
            for coin in mentioned_coins:
                if not config.is_coin_supported(coin):
                    continue
                
                symbol = config.get_trade_symbol(coin)
                
                # Determine action based on sentiment
                action = "hold"
                reasoning = f"Neutral sentiment for {coin}"
                
                if sentiment == "positive" and sentiment_score > self.sentiment_threshold:
                    action = "buy"
                    reasoning = f"Positive sentiment ({sentiment_score:.2f}) for {coin} from news"
                elif sentiment == "negative" and sentiment_score < -self.sentiment_threshold:
                    # Only sell if we have a position
                    if self._has_open_position(symbol):
                        action = "sell"
                        reasoning = f"Negative sentiment ({sentiment_score:.2f}) for {coin}, closing position"
                
                if action != "hold":
                    signal = TradingSignal(
                        symbol=symbol,
                        action=action,
                        confidence=confidence,
                        sentiment=sentiment,
                        news_id=news_data.get('id'),
                        reasoning=reasoning
                    )
                    signals.append(signal)
                    
        except Exception as e:
            logger.error(f"Error analyzing news for trading: {e}")
        
        return signals
    
    def _has_open_position(self, symbol: str) -> bool:
        """Check if we have an open position for the symbol."""
        open_positions = data_store.get_open_positions()
        return any(pos.get('symbol') == symbol for pos in open_positions)
    
    def execute_signal(self, signal: TradingSignal) -> Optional[Dict[str, Any]]:
        """Execute a trading signal."""
        try:
            logger.info(f"Executing signal: {signal.action} {signal.symbol} (confidence: {signal.confidence:.2f})")
            
            if signal.action == "buy":
                return self._execute_buy(signal)
            elif signal.action == "sell":
                return self._execute_sell(signal)
            else:
                logger.debug(f"No action for signal: {signal.action}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            raise TradingError(f"Failed to execute signal: {e}")
    
    def _execute_buy(self, signal: TradingSignal) -> Optional[Dict[str, Any]]:
        """Execute buy order."""
        try:
            # Check risk limits
            trade_amount = config.trade_amounts.get(signal.symbol, config.trade_amount_usdt)
            
            if not self.risk_manager.check_trade_limits(trade_amount):
                logger.warning(f"Risk limits prevent buy order for {signal.symbol}")
                return None
            
            if not self.risk_manager.can_open_position(signal.symbol):
                logger.warning(f"Cannot open position for {signal.symbol}")
                return None
            
            # Calculate quantity to buy
            quantity = binance_api.calculate_buy_quantity(signal.symbol, trade_amount)
            current_price = binance_api.get_price(signal.symbol)
            
            # Execute buy order
            order = binance_api.create_market_buy_order(signal.symbol, quantity)
            
            # Record order
            order_data = {
                'binance_order_id': str(order['orderId']),
                'symbol': signal.symbol,
                'side': 'BUY',
                'quantity': quantity,
                'price': current_price,
                'status': order['status'],
                'executed_quantity': float(order['executedQty']),
                'executed_price': float(order['price']),
                'news_item_id': signal.news_id
            }
            order_id = data_store.save_trading_order(order_data)
            
            # Create position
            stop_loss_price = current_price * (1 - config.stop_loss_percentage)
            position_data = {
                'symbol': signal.symbol,
                'quantity': quantity,
                'entry_price': current_price,
                'current_price': current_price,
                'stop_loss_price': stop_loss_price,
                'stop_loss_percentage': config.stop_loss_percentage,
                'status': 'open',
                'is_monitoring': True,
                'entry_order_id': order_id,
                'news_item_id': signal.news_id
            }
            position_id = data_store.save_position(position_data)
            
            # Update order with position ID
            data_store.update_trading_order(order_id, {'position_id': position_id})
            
            # Record trade for risk management
            self.risk_manager.record_trade()
            
            logger.info(
                f"Buy order executed: {quantity:.6f} {signal.symbol} at {current_price:.2f} "
                f"(Stop loss: {stop_loss_price:.2f})"
            )
            
            return {
                'order_id': order_id,
                'position_id': position_id,
                'order': order
            }
            
        except Exception as e:
            logger.error(f"Error executing buy order: {e}")
            raise TradingError(f"Buy execution failed: {e}")
    
    def _execute_sell(self, signal: TradingSignal) -> Optional[Dict[str, Any]]:
        """Execute sell order for existing position."""
        try:
            # Find open position for this symbol
            open_positions = data_store.get_open_positions()
            position = None
            for pos in open_positions:
                if pos.get('symbol') == signal.symbol:
                    position = pos
                    break
            
            if not position:
                logger.warning(f"No open position found for {signal.symbol}")
                return None
            
            # Execute sell order
            quantity = position['quantity']
            current_price = binance_api.get_price(signal.symbol)
            
            order = binance_api.create_market_sell_order(signal.symbol, quantity)
            
            # Record sell order
            order_data = {
                'binance_order_id': str(order['orderId']),
                'symbol': signal.symbol,
                'side': 'SELL',
                'quantity': quantity,
                'price': current_price,
                'status': order['status'],
                'executed_quantity': float(order['executedQty']),
                'executed_price': float(order['price']),
                'position_id': position['id'],
                'news_item_id': signal.news_id
            }
            order_id = data_store.save_trading_order(order_data)
            
            # Calculate P&L
            entry_price = position['entry_price']
            realized_pnl = (current_price - entry_price) * quantity
            
            # Close position
            position_updates = {
                'status': 'closed',
                'current_price': current_price,
                'realized_pnl': realized_pnl,
                'exit_order_id': order_id,
                'is_monitoring': False
            }
            data_store.update_position(position['id'], position_updates)
            
            # Record trade for risk management
            self.risk_manager.record_trade(realized_pnl)
            
            logger.info(
                f"Sell order executed: {quantity:.6f} {signal.symbol} at {current_price:.2f} "
                f"(P&L: {realized_pnl:.2f})"
            )
            
            return {
                'order_id': order_id,
                'position_id': position['id'],
                'pnl': realized_pnl,
                'order': order
            }
            
        except Exception as e:
            logger.error(f"Error executing sell order: {e}")
            raise TradingError(f"Sell execution failed: {e}")


class TradingEngine:
    """Main trading engine that coordinates all trading activities."""
    
    def __init__(self):
        self.strategy = TradingStrategy()
        self.running = False
    
    def process_news_for_trading(self, news_data: Dict[str, Any]):
        """Process news item for potential trading opportunities."""
        try:
            # Generate trading signals
            signals = self.strategy.analyze_news_for_trading(news_data)
            
            if not signals:
                logger.debug(f"No trading signals generated from news: {news_data.get('title', '')[:50]}...")
                return
            
            # Execute signals
            for signal in signals:
                try:
                    result = self.strategy.execute_signal(signal)
                    if result:
                        # Mark news as having triggered a trade
                        data_store.update_news_item(news_data['id'], {'triggered_trade': True})
                        logger.info(f"Trade executed based on news sentiment")
                        
                except Exception as e:
                    logger.error(f"Error executing trading signal: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing news for trading: {e}")
    
    def get_trading_summary(self) -> Dict[str, Any]:
        """Get summary of trading activity."""
        try:
            # Get recent orders and positions
            orders = data_store.get_trading_orders(limit=50)
            positions = data_store.get_all_positions(limit=50)
            open_positions = data_store.get_open_positions()
            
            # Calculate summary statistics
            total_trades = len(orders)
            open_positions_count = len(open_positions)
            
            total_pnl = sum(pos.get('realized_pnl', 0) for pos in positions)
            
            # Get account balance
            try:
                account_info = binance_api.get_account_info()
                balances = {bal['asset']: float(bal['free']) for bal in account_info['balances']}
            except Exception:
                balances = {}
            
            return {
                'total_trades': total_trades,
                'open_positions': open_positions_count,
                'total_pnl': total_pnl,
                'balances': balances,
                'recent_orders': orders[:10],
                'open_positions': open_positions,
                'risk_stats': {
                    'daily_trades': self.strategy.risk_manager.daily_trades,
                    'daily_loss': self.strategy.risk_manager.daily_loss,
                    'max_daily_trades': config.max_daily_trades,
                    'daily_loss_limit': config.daily_loss_limit
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting trading summary: {e}")
            return {'error': str(e)}


# Global trading engine
trading_engine = TradingEngine()


def process_news_for_trading(news_data: Dict[str, Any]):
    """Process news for trading opportunities."""
    trading_engine.process_news_for_trading(news_data)


def get_trading_summary() -> Dict[str, Any]:
    """Get trading summary."""
    return trading_engine.get_trading_summary()