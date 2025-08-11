"""
Simple data storage using JSON files (for development without external dependencies).
This will be replaced with proper database support once dependencies are available.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from utils.logging import get_logger

logger = get_logger(__name__)


class SimpleDataStore:
    """Simple JSON-based data storage."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize data files
        self.news_file = self.data_dir / "news_items.json"
        self.orders_file = self.data_dir / "trading_orders.json"
        self.positions_file = self.data_dir / "positions.json"
        self.metrics_file = self.data_dir / "system_metrics.json"
        self.config_file = self.data_dir / "config_items.json"
        
        # Ensure all files exist
        for file_path in [self.news_file, self.orders_file, self.positions_file, 
                         self.metrics_file, self.config_file]:
            if not file_path.exists():
                self._save_json(file_path, [])
    
    def _load_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load data from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_json(self, file_path: Path, data: List[Dict[str, Any]]):
        """Save data to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def _generate_id(self, data: List[Dict[str, Any]]) -> int:
        """Generate next ID for new record."""
        if not data:
            return 1
        return max(item.get('id', 0) for item in data) + 1
    
    # News items
    def save_news_item(self, news_data: Dict[str, Any]) -> int:
        """Save a news item."""
        news_items = self._load_json(self.news_file)
        news_data['id'] = self._generate_id(news_items)
        news_data['created_at'] = datetime.utcnow().isoformat()
        news_data['updated_at'] = datetime.utcnow().isoformat()
        news_items.append(news_data)
        self._save_json(self.news_file, news_items)
        logger.debug(f"Saved news item with ID {news_data['id']}")
        return news_data['id']
    
    def get_news_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent news items."""
        news_items = self._load_json(self.news_file)
        return sorted(news_items, key=lambda x: x.get('created_at', ''), reverse=True)[:limit]
    
    def update_news_item(self, news_id: int, updates: Dict[str, Any]):
        """Update a news item."""
        news_items = self._load_json(self.news_file)
        for item in news_items:
            if item.get('id') == news_id:
                item.update(updates)
                item['updated_at'] = datetime.utcnow().isoformat()
                break
        self._save_json(self.news_file, news_items)
    
    # Trading orders
    def save_trading_order(self, order_data: Dict[str, Any]) -> int:
        """Save a trading order."""
        orders = self._load_json(self.orders_file)
        order_data['id'] = self._generate_id(orders)
        order_data['created_at'] = datetime.utcnow().isoformat()
        order_data['updated_at'] = datetime.utcnow().isoformat()
        orders.append(order_data)
        self._save_json(self.orders_file, orders)
        logger.debug(f"Saved trading order with ID {order_data['id']}")
        return order_data['id']
    
    def get_trading_orders(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trading orders."""
        orders = self._load_json(self.orders_file)
        return sorted(orders, key=lambda x: x.get('created_at', ''), reverse=True)[:limit]
    
    def update_trading_order(self, order_id: int, updates: Dict[str, Any]):
        """Update a trading order."""
        orders = self._load_json(self.orders_file)
        for order in orders:
            if order.get('id') == order_id:
                order.update(updates)
                order['updated_at'] = datetime.utcnow().isoformat()
                break
        self._save_json(self.orders_file, orders)
    
    # Positions
    def save_position(self, position_data: Dict[str, Any]) -> int:
        """Save a position."""
        positions = self._load_json(self.positions_file)
        position_data['id'] = self._generate_id(positions)
        position_data['opened_at'] = datetime.utcnow().isoformat()
        position_data['updated_at'] = datetime.utcnow().isoformat()
        positions.append(position_data)
        self._save_json(self.positions_file, positions)
        logger.debug(f"Saved position with ID {position_data['id']}")
        return position_data['id']
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions."""
        positions = self._load_json(self.positions_file)
        return [p for p in positions if p.get('status') == 'open']
    
    def get_all_positions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all positions."""
        positions = self._load_json(self.positions_file)
        return sorted(positions, key=lambda x: x.get('opened_at', ''), reverse=True)[:limit]
    
    def update_position(self, position_id: int, updates: Dict[str, Any]):
        """Update a position."""
        positions = self._load_json(self.positions_file)
        for position in positions:
            if position.get('id') == position_id:
                position.update(updates)
                position['updated_at'] = datetime.utcnow().isoformat()
                if updates.get('status') in ['closed', 'stopped']:
                    position['closed_at'] = datetime.utcnow().isoformat()
                break
        self._save_json(self.positions_file, positions)
    
    # System metrics
    def save_system_metrics(self, metrics_data: Dict[str, Any]) -> int:
        """Save system metrics."""
        metrics = self._load_json(self.metrics_file)
        metrics_data['id'] = self._generate_id(metrics)
        metrics_data['created_at'] = datetime.utcnow().isoformat()
        metrics.append(metrics_data)
        self._save_json(self.metrics_file, metrics)
        return metrics_data['id']
    
    def get_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """Get latest system metrics."""
        metrics = self._load_json(self.metrics_file)
        if metrics:
            return sorted(metrics, key=lambda x: x.get('created_at', ''), reverse=True)[0]
        return None
    
    # Configuration
    def save_config_item(self, key: str, value: Any, description: str = "", data_type: str = "string"):
        """Save or update a configuration item."""
        config_items = self._load_json(self.config_file)
        
        # Check if key exists
        for item in config_items:
            if item.get('key') == key:
                item.update({
                    'value': json.dumps(value) if data_type == 'json' else str(value),
                    'description': description,
                    'data_type': data_type,
                    'updated_at': datetime.utcnow().isoformat()
                })
                self._save_json(self.config_file, config_items)
                return
        
        # Add new item
        new_item = {
            'id': self._generate_id(config_items),
            'key': key,
            'value': json.dumps(value) if data_type == 'json' else str(value),
            'description': description,
            'data_type': data_type,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        config_items.append(new_item)
        self._save_json(self.config_file, config_items)
    
    def get_config_item(self, key: str) -> Optional[Any]:
        """Get a configuration item value."""
        config_items = self._load_json(self.config_file)
        for item in config_items:
            if item.get('key') == key:
                value = item.get('value', '')
                data_type = item.get('data_type', 'string')
                
                if data_type == 'json':
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return None
                elif data_type == 'bool':
                    return value.lower() in ('true', '1', 'yes')
                elif data_type == 'int':
                    try:
                        return int(value)
                    except ValueError:
                        return 0
                elif data_type == 'float':
                    try:
                        return float(value)
                    except ValueError:
                        return 0.0
                else:
                    return value
        return None


# Global data store instance
data_store = SimpleDataStore()