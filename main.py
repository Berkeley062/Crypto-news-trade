"""
Main application entry point for the crypto trading system.
Coordinates all modules and provides the main execution loop.
"""

import signal
import sys
import time
import threading
from datetime import datetime
from typing import Dict, Any

from config import config
from simple_storage import data_store
from modules.news_collector import start_news_collection, stop_news_collection, add_news_handler
from modules.sentiment_analyzer import process_news_sentiment, process_all_pending_sentiment
from modules.trading_strategy import process_news_for_trading, get_trading_summary
from modules.stop_loss_monitor import start_stop_loss_monitoring, stop_stop_loss_monitoring
from utils.logging import get_logger

logger = get_logger(__name__)


class CryptoTradingSystem:
    """Main crypto trading system coordinator."""
    
    def __init__(self):
        self.running = False
        self.news_processing_enabled = True
        self.trading_enabled = True
        self.stop_loss_enabled = True
        
        # Statistics
        self.start_time = None
        self.news_processed = 0
        self.trades_executed = 0
        
    def initialize(self):
        """Initialize the trading system."""
        logger.info("Initializing Crypto Trading System...")
        
        # Initialize data storage
        logger.info("Checking data storage...")
        
        # Save initial configuration
        data_store.save_config_item(
            "system_initialized", 
            True, 
            "System initialization flag", 
            "bool"
        )
        data_store.save_config_item(
            "last_startup", 
            datetime.utcnow().isoformat(), 
            "Last system startup time", 
            "string"
        )
        
        # Set up news processing callback
        add_news_handler(self._handle_news_item)
        
        logger.info("System initialization completed")
    
    def start(self):
        """Start the trading system."""
        if self.running:
            logger.warning("System is already running")
            return
        
        self.running = True
        self.start_time = datetime.utcnow()
        
        logger.info("Starting Crypto Trading System...")
        logger.info(f"Configuration: {config.environment} mode, testnet: {config.binance_testnet}")
        
        try:
            # Process any pending sentiment analysis first
            if self.news_processing_enabled:
                logger.info("Processing pending news sentiment...")
                process_all_pending_sentiment()
            
            # Start stop-loss monitoring
            if self.stop_loss_enabled:
                logger.info("Starting stop-loss monitoring...")
                start_stop_loss_monitoring()
            
            # Start news collection
            if self.news_processing_enabled:
                logger.info("Starting news collection...")
                start_news_collection()
            
            logger.info("Crypto Trading System started successfully")
            
            # Log system status
            self._log_system_status()
            
        except Exception as e:
            logger.error(f"Error starting system: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop the trading system."""
        if not self.running:
            return
        
        logger.info("Stopping Crypto Trading System...")
        
        try:
            # Stop news collection
            stop_news_collection()
            
            # Stop stop-loss monitoring
            stop_stop_loss_monitoring()
            
            self.running = False
            
            # Log final statistics
            self._log_final_statistics()
            
            logger.info("Crypto Trading System stopped")
            
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
    
    def _handle_news_item(self, news_item):
        """Handle incoming news item."""
        try:
            # Convert news item to dict for processing
            news_data = news_item.to_dict()
            
            # Save to storage first to get an ID
            if 'id' not in news_data:
                news_id = data_store.save_news_item(news_data)
                news_data['id'] = news_id
            
            # Process sentiment if not already processed
            if not news_data.get('processed', False):
                logger.debug(f"Processing sentiment for news: {news_item.title[:50]}...")
                news_data = process_news_sentiment(news_data)
                
                # Update in storage
                data_store.update_news_item(news_data['id'], news_data)
            
            # Process for trading if trading is enabled
            if self.trading_enabled and news_data.get('processed', False):
                logger.debug(f"Processing for trading: {news_item.title[:50]}...")
                process_news_for_trading(news_data)
            
            self.news_processed += 1
            
        except Exception as e:
            logger.error(f"Error handling news item: {e}")
    
    def _log_system_status(self):
        """Log current system status."""
        try:
            # Get trading summary
            trading_summary = get_trading_summary()
            
            # Get recent news count
            recent_news = data_store.get_news_items(limit=10)
            
            logger.info("=== System Status ===")
            logger.info(f"Running: {self.running}")
            logger.info(f"News processed: {self.news_processed}")
            logger.info(f"Recent news items: {len(recent_news)}")
            logger.info(f"Open positions: {trading_summary.get('open_positions', 0)}")
            logger.info(f"Total trades: {trading_summary.get('total_trades', 0)}")
            logger.info(f"Total P&L: {trading_summary.get('total_pnl', 0):.2f}")
            logger.info("==================")
            
        except Exception as e:
            logger.error(f"Error logging system status: {e}")
    
    def _log_final_statistics(self):
        """Log final system statistics."""
        try:
            uptime = (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
            
            logger.info("=== Final Statistics ===")
            logger.info(f"Uptime: {uptime:.0f} seconds")
            logger.info(f"News processed: {self.news_processed}")
            logger.info("========================")
            
            # Save metrics to storage
            metrics_data = {
                'date': datetime.utcnow().isoformat(),
                'uptime_seconds': int(uptime),
                'news_processed': self.news_processed,
                'trades_triggered': 0,  # Will be updated by trading module
                'errors_count': 0  # Basic implementation
            }
            data_store.save_system_metrics(metrics_data)
            
        except Exception as e:
            logger.error(f"Error logging final statistics: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        try:
            trading_summary = get_trading_summary()
            recent_news = data_store.get_news_items(limit=5)
            
            uptime = (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
            
            return {
                'running': self.running,
                'uptime_seconds': int(uptime),
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'news_processed': self.news_processed,
                'recent_news_count': len(recent_news),
                'trading_summary': trading_summary,
                'modules': {
                    'news_processing': self.news_processing_enabled,
                    'trading': self.trading_enabled,
                    'stop_loss': self.stop_loss_enabled
                },
                'config': {
                    'environment': config.environment,
                    'testnet': config.binance_testnet,
                    'supported_coins': config.supported_coins,
                    'stop_loss_percentage': config.stop_loss_percentage
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def run_forever(self):
        """Run the system until interrupted."""
        try:
            logger.info("System is running. Press Ctrl+C to stop.")
            
            # Set up signal handlers
            def signal_handler(signum, frame):
                logger.info(f"Received signal {signum}, stopping system...")
                self.stop()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Main loop
            while self.running:
                time.sleep(60)  # Check every minute
                
                # Periodic status logging
                if hasattr(self, '_last_status_log'):
                    time_since_log = (datetime.utcnow() - self._last_status_log).total_seconds()
                    if time_since_log >= 300:  # Log every 5 minutes
                        self._log_system_status()
                        self._last_status_log = datetime.utcnow()
                else:
                    self._last_status_log = datetime.utcnow()
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping system...")
            self.stop()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            self.stop()
            raise


# Global system instance
trading_system = CryptoTradingSystem()


def main():
    """Main application entry point."""
    try:
        # Initialize system
        trading_system.initialize()
        
        # Start system
        trading_system.start()
        
        # Run forever (until interrupted)
        trading_system.run_forever()
        
    except Exception as e:
        logger.error(f"Fatal error in main application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()