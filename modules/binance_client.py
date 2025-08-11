"""
Mock Binance API client for development and testing.
This simulates the python-binance library functionality without requiring external dependencies.
"""

import json
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
from decimal import Decimal

from config import config
from utils.logging import get_logger
from exceptions import BinanceAPIError, TradingError

logger = get_logger(__name__)


class MockBinanceClient:
    """Mock Binance client for testing and development."""
    
    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Mock account state
        self.account_balance = {
            "USDT": 1000.0,  # Starting with 1000 USDT
            "BTC": 0.0,
            "ETH": 0.0,
            "BNB": 0.0,
            "ADA": 0.0,
            "SOL": 0.0
        }
        
        # Mock order tracking
        self.orders = {}
        self.order_id_counter = 1
        
        # Mock price data (simulated real-time prices)
        self.mock_prices = {
            "BTCUSDT": 45000.0,
            "ETHUSDT": 2800.0,
            "BNBUSDT": 350.0,
            "ADAUSDT": 0.85,
            "SOLUSDT": 95.0
        }
        
        logger.info(f"Initialized Mock Binance Client (testnet: {testnet})")
    
    def get_account(self) -> Dict[str, Any]:
        """Get account information."""
        balances = []
        for asset, amount in self.account_balance.items():
            balances.append({
                "asset": asset,
                "free": str(amount),
                "locked": "0.0"
            })
        
        return {
            "makerCommission": 10,
            "takerCommission": 10,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": True,
            "canWithdraw": True,
            "canDeposit": True,
            "updateTime": int(time.time() * 1000),
            "accountType": "SPOT",
            "balances": balances
        }
    
    def get_symbol_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker price for a symbol."""
        if symbol not in self.mock_prices:
            raise BinanceAPIError(f"Symbol {symbol} not found")
        
        base_price = self.mock_prices[symbol]
        # Add small random variation (±2%)
        variation = random.uniform(-0.02, 0.02)
        current_price = base_price * (1 + variation)
        
        return {
            "symbol": symbol,
            "price": str(current_price)
        }
    
    def get_all_tickers(self) -> List[Dict[str, Any]]:
        """Get all ticker prices."""
        tickers = []
        for symbol in self.mock_prices:
            ticker = self.get_symbol_ticker(symbol)
            tickers.append(ticker)
        return tickers
    
    def create_order(
        self,
        symbol: str,
        side: str,
        type: str,
        quantity: float,
        price: Optional[float] = None,
        timeInForce: str = "GTC",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new order."""
        try:
            # Validate inputs
            if symbol not in self.mock_prices:
                raise BinanceAPIError(f"Symbol {symbol} not supported")
            
            if side not in ["BUY", "SELL"]:
                raise BinanceAPIError(f"Invalid side: {side}")
            
            if type not in ["MARKET", "LIMIT"]:
                raise BinanceAPIError(f"Order type {type} not supported in mock")
            
            # Get current price
            current_price = float(self.get_symbol_ticker(symbol)["price"])
            execution_price = price if type == "LIMIT" else current_price
            
            # Generate order ID
            order_id = self.order_id_counter
            self.order_id_counter += 1
            
            # Calculate costs and validate balance
            base_asset = symbol.replace("USDT", "")
            quote_asset = "USDT"
            
            if side == "BUY":
                cost = quantity * execution_price
                if self.account_balance.get(quote_asset, 0) < cost:
                    raise BinanceAPIError("Insufficient balance for buy order")
                
                # Execute immediately (mock)
                self.account_balance[quote_asset] -= cost
                self.account_balance[base_asset] = self.account_balance.get(base_asset, 0) + quantity
                status = "FILLED"
                
            else:  # SELL
                if self.account_balance.get(base_asset, 0) < quantity:
                    raise BinanceAPIError("Insufficient balance for sell order")
                
                # Execute immediately (mock)
                self.account_balance[base_asset] -= quantity
                proceeds = quantity * execution_price
                self.account_balance[quote_asset] = self.account_balance.get(quote_asset, 0) + proceeds
                status = "FILLED"
            
            # Create order record
            order = {
                "symbol": symbol,
                "orderId": order_id,
                "orderListId": -1,
                "clientOrderId": f"mock_{order_id}",
                "transactTime": int(time.time() * 1000),
                "price": str(execution_price),
                "origQty": str(quantity),
                "executedQty": str(quantity),
                "cummulativeQuoteQty": str(quantity * execution_price),
                "status": status,
                "timeInForce": timeInForce,
                "type": type,
                "side": side,
                "fills": [
                    {
                        "price": str(execution_price),
                        "qty": str(quantity),
                        "commission": "0.0",
                        "commissionAsset": base_asset,
                        "tradeId": order_id * 100
                    }
                ]
            }
            
            self.orders[order_id] = order
            
            logger.info(
                f"Mock order executed: {side} {quantity} {symbol} at {execution_price:.2f}"
            )
            
            return order
            
        except Exception as e:
            logger.error(f"Error creating mock order: {e}")
            raise BinanceAPIError(f"Failed to create order: {e}")
    
    def get_order(self, symbol: str, orderId: int) -> Dict[str, Any]:
        """Get order status."""
        if orderId not in self.orders:
            raise BinanceAPIError(f"Order {orderId} not found")
        
        return self.orders[orderId]
    
    def cancel_order(self, symbol: str, orderId: int) -> Dict[str, Any]:
        """Cancel an order."""
        if orderId not in self.orders:
            raise BinanceAPIError(f"Order {orderId} not found")
        
        order = self.orders[orderId]
        order["status"] = "CANCELED"
        
        logger.info(f"Mock order canceled: {orderId}")
        return order
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open orders."""
        open_orders = []
        for order in self.orders.values():
            if order["status"] in ["NEW", "PARTIALLY_FILLED"]:
                if symbol is None or order["symbol"] == symbol:
                    open_orders.append(order)
        return open_orders


class BinanceAPIWrapper:
    """Wrapper for Binance API that can use either real or mock client."""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate client based on configuration."""
        try:
            # For now, always use mock client since we don't have python-binance installed
            self.client = MockBinanceClient(
                api_key=config.binance_api_key,
                api_secret=config.binance_api_secret,
                testnet=config.binance_testnet
            )
            logger.info("Initialized Binance API wrapper with mock client")
            
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            raise BinanceAPIError(f"Client initialization failed: {e}")
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        try:
            return self.client.get_account()
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            raise BinanceAPIError(f"Failed to get account info: {e}")
    
    def get_balance(self, asset: str) -> float:
        """Get balance for specific asset."""
        try:
            account = self.get_account_info()
            for balance in account["balances"]:
                if balance["asset"] == asset:
                    return float(balance["free"])
            return 0.0
        except Exception as e:
            logger.error(f"Error getting balance for {asset}: {e}")
            raise BinanceAPIError(f"Failed to get balance: {e}")
    
    def get_price(self, symbol: str) -> float:
        """Get current price for symbol."""
        try:
            ticker = self.client.get_symbol_ticker(symbol)
            return float(ticker["price"])
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            raise BinanceAPIError(f"Failed to get price: {e}")
    
    def create_market_buy_order(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Create market buy order."""
        try:
            return self.client.create_order(
                symbol=symbol,
                side="BUY",
                type="MARKET",
                quantity=quantity
            )
        except Exception as e:
            logger.error(f"Error creating market buy order: {e}")
            raise BinanceAPIError(f"Failed to create buy order: {e}")
    
    def create_market_sell_order(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Create market sell order."""
        try:
            return self.client.create_order(
                symbol=symbol,
                side="SELL",
                type="MARKET",
                quantity=quantity
            )
        except Exception as e:
            logger.error(f"Error creating market sell order: {e}")
            raise BinanceAPIError(f"Failed to create sell order: {e}")
    
    def create_limit_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        price: float
    ) -> Dict[str, Any]:
        """Create limit order."""
        try:
            return self.client.create_order(
                symbol=symbol,
                side=side,
                type="LIMIT",
                quantity=quantity,
                price=price,
                timeInForce="GTC"
            )
        except Exception as e:
            logger.error(f"Error creating limit order: {e}")
            raise BinanceAPIError(f"Failed to create limit order: {e}")
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order status."""
        try:
            return self.client.get_order(symbol, order_id)
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            raise BinanceAPIError(f"Failed to get order status: {e}")
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel order."""
        try:
            return self.client.cancel_order(symbol, order_id)
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            raise BinanceAPIError(f"Failed to cancel order: {e}")
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open orders."""
        try:
            return self.client.get_open_orders(symbol)
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            raise BinanceAPIError(f"Failed to get open orders: {e}")
    
    def calculate_buy_quantity(self, symbol: str, usdt_amount: float) -> float:
        """Calculate quantity to buy with given USDT amount."""
        try:
            price = self.get_price(symbol)
            quantity = usdt_amount / price
            
            # Round to appropriate precision (mock implementation)
            if "BTC" in symbol:
                return round(quantity, 6)
            elif "ETH" in symbol:
                return round(quantity, 5)
            else:
                return round(quantity, 4)
                
        except Exception as e:
            logger.error(f"Error calculating buy quantity: {e}")
            raise BinanceAPIError(f"Failed to calculate buy quantity: {e}")


# Global Binance API wrapper
binance_api = BinanceAPIWrapper()