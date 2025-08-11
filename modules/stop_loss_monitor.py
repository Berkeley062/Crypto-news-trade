"""
Stop-loss monitoring module for automatic position management.
Monitors open positions and triggers stop-loss orders when conditions are met.
"""

import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from config import config
from simple_storage import data_store
from modules.binance_client import binance_api
from utils.logging import get_logger
from exceptions import StopLossError, TradingError

logger = get_logger(__name__)


class PositionMonitor:
    """Monitors a single position for stop-loss conditions."""
    
    def __init__(self, position_data: Dict[str, Any]):
        self.position_id = position_data['id']
        self.symbol = position_data['symbol']
        self.quantity = position_data['quantity']
        self.entry_price = position_data['entry_price']
        self.stop_loss_price = position_data['stop_loss_price']
        self.stop_loss_percentage = position_data.get('stop_loss_percentage', config.stop_loss_percentage)
        
        self.running = False
        self.thread = None
        self.check_interval = 10  # Check every 10 seconds
        self.last_price_update = datetime.utcnow()
    
    def start(self):
        """Start monitoring this position."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started monitoring position {self.position_id} for {self.symbol}")
    
    def stop(self):
        """Stop monitoring this position."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"Stopped monitoring position {self.position_id}")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Check if position is still open
                position = self._get_current_position()
                if not position or position.get('status') != 'open':
                    logger.info(f"Position {self.position_id} is no longer open, stopping monitor")
                    break
                
                # Get current price
                current_price = binance_api.get_price(self.symbol)
                
                # Update position with current price and P&L
                unrealized_pnl = (current_price - self.entry_price) * self.quantity
                position_updates = {
                    'current_price': current_price,
                    'unrealized_pnl': unrealized_pnl
                }
                data_store.update_position(self.position_id, position_updates)
                
                # Check stop-loss condition
                if current_price <= self.stop_loss_price:
                    logger.warning(
                        f"Stop-loss triggered for {self.symbol}: "
                        f"Price {current_price:.4f} <= Stop-loss {self.stop_loss_price:.4f}"
                    )
                    self._execute_stop_loss(current_price)
                    break
                
                # Log price updates periodically
                time_since_update = (datetime.utcnow() - self.last_price_update).total_seconds()
                if time_since_update >= 60:  # Log every minute
                    logger.debug(
                        f"Position {self.position_id} {self.symbol}: "
                        f"Price {current_price:.4f}, P&L {unrealized_pnl:.2f}"
                    )
                    self.last_price_update = datetime.utcnow()
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in position monitor for {self.position_id}: {e}")
                time.sleep(self.check_interval)
        
        self.running = False
    
    def _get_current_position(self) -> Optional[Dict[str, Any]]:
        """Get current position data from storage."""
        try:
            all_positions = data_store.get_all_positions(limit=1000)
            for position in all_positions:
                if position.get('id') == self.position_id:
                    return position
            return None
        except Exception as e:
            logger.error(f"Error getting position {self.position_id}: {e}")
            return None
    
    def _execute_stop_loss(self, current_price: float):
        """Execute stop-loss order."""
        try:
            logger.info(f"Executing stop-loss for position {self.position_id}")
            
            # Create market sell order
            order = binance_api.create_market_sell_order(self.symbol, self.quantity)
            
            # Record the stop-loss order
            order_data = {
                'binance_order_id': str(order['orderId']),
                'symbol': self.symbol,
                'side': 'SELL',
                'quantity': self.quantity,
                'price': current_price,
                'status': order['status'],
                'executed_quantity': float(order['executedQty']),
                'executed_price': float(order['price']),
                'position_id': self.position_id
            }
            order_id = data_store.save_trading_order(order_data)
            
            # Calculate realized P&L
            executed_price = float(order['price'])
            realized_pnl = (executed_price - self.entry_price) * self.quantity
            
            # Update position status
            position_updates = {
                'status': 'stopped',
                'current_price': executed_price,
                'realized_pnl': realized_pnl,
                'exit_order_id': order_id,
                'is_monitoring': False
            }
            data_store.update_position(self.position_id, position_updates)
            
            logger.info(
                f"Stop-loss executed for {self.symbol}: "
                f"Sold {self.quantity:.6f} at {executed_price:.4f}, "
                f"P&L: {realized_pnl:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Error executing stop-loss for position {self.position_id}: {e}")
            raise StopLossError(f"Failed to execute stop-loss: {e}")


class StopLossManager:
    """Manages stop-loss monitoring for all open positions."""
    
    def __init__(self):
        self.monitors: Dict[int, PositionMonitor] = {}
        self.running = False
        self.management_thread = None
        self.check_interval = 30  # Check for new positions every 30 seconds
    
    def start(self):
        """Start the stop-loss manager."""
        if self.running:
            return
        
        self.running = True
        
        # Start monitoring existing open positions
        self._start_existing_monitors()
        
        # Start management thread to monitor for new positions
        self.management_thread = threading.Thread(target=self._management_loop, daemon=True)
        self.management_thread.start()
        
        logger.info("Stop-loss manager started")
    
    def stop(self):
        """Stop the stop-loss manager."""
        self.running = False
        
        # Stop all position monitors
        for monitor in list(self.monitors.values()):
            monitor.stop()
        self.monitors.clear()
        
        # Stop management thread
        if self.management_thread:
            self.management_thread.join(timeout=10)
        
        logger.info("Stop-loss manager stopped")
    
    def _start_existing_monitors(self):
        """Start monitors for existing open positions."""
        try:
            open_positions = data_store.get_open_positions()
            for position in open_positions:
                if position.get('is_monitoring', True):
                    self._add_position_monitor(position)
        except Exception as e:
            logger.error(f"Error starting existing monitors: {e}")
    
    def _management_loop(self):
        """Main management loop to check for new positions."""
        while self.running:
            try:
                # Check for new open positions that need monitoring
                open_positions = data_store.get_open_positions()
                
                for position in open_positions:
                    position_id = position.get('id')
                    is_monitoring = position.get('is_monitoring', True)
                    
                    # Add monitor if not already monitoring
                    if is_monitoring and position_id not in self.monitors:
                        self._add_position_monitor(position)
                
                # Remove monitors for positions that are no longer open
                current_open_ids = {pos.get('id') for pos in open_positions 
                                  if pos.get('is_monitoring', True)}
                
                monitors_to_remove = []
                for position_id, monitor in self.monitors.items():
                    if position_id not in current_open_ids:
                        monitor.stop()
                        monitors_to_remove.append(position_id)
                
                for position_id in monitors_to_remove:
                    del self.monitors[position_id]
                    logger.info(f"Removed monitor for position {position_id}")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in stop-loss management loop: {e}")
                time.sleep(self.check_interval)
    
    def _add_position_monitor(self, position: Dict[str, Any]):
        """Add a position monitor."""
        try:
            position_id = position.get('id')
            if position_id in self.monitors:
                return
            
            monitor = PositionMonitor(position)
            monitor.start()
            self.monitors[position_id] = monitor
            
            logger.info(f"Added stop-loss monitor for position {position_id} ({position['symbol']})")
            
        except Exception as e:
            logger.error(f"Error adding position monitor: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get status of all monitored positions."""
        try:
            status = {
                'total_monitors': len(self.monitors),
                'running': self.running,
                'monitored_positions': []
            }
            
            for position_id, monitor in self.monitors.items():
                position_info = {
                    'position_id': position_id,
                    'symbol': monitor.symbol,
                    'entry_price': monitor.entry_price,
                    'stop_loss_price': monitor.stop_loss_price,
                    'quantity': monitor.quantity,
                    'running': monitor.running
                }
                status['monitored_positions'].append(position_info)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting monitoring status: {e}")
            return {'error': str(e)}
    
    def update_stop_loss(self, position_id: int, new_stop_loss_price: float):
        """Update stop-loss price for a position."""
        try:
            if position_id in self.monitors:
                monitor = self.monitors[position_id]
                old_price = monitor.stop_loss_price
                monitor.stop_loss_price = new_stop_loss_price
                
                # Update in storage
                data_store.update_position(position_id, {'stop_loss_price': new_stop_loss_price})
                
                logger.info(
                    f"Updated stop-loss for position {position_id}: "
                    f"{old_price:.4f} -> {new_stop_loss_price:.4f}"
                )
            else:
                logger.warning(f"No monitor found for position {position_id}")
                
        except Exception as e:
            logger.error(f"Error updating stop-loss: {e}")
            raise StopLossError(f"Failed to update stop-loss: {e}")


# Global stop-loss manager
stop_loss_manager = StopLossManager()


def start_stop_loss_monitoring():
    """Start stop-loss monitoring."""
    stop_loss_manager.start()


def stop_stop_loss_monitoring():
    """Stop stop-loss monitoring."""
    stop_loss_manager.stop()


def get_stop_loss_status() -> Dict[str, Any]:
    """Get stop-loss monitoring status."""
    return stop_loss_manager.get_monitoring_status()


def update_position_stop_loss(position_id: int, new_stop_loss_price: float):
    """Update stop-loss price for a position."""
    stop_loss_manager.update_stop_loss(position_id, new_stop_loss_price)