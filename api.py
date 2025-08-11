"""
REST API for the crypto trading system web interface.
Provides endpoints for monitoring and controlling the trading system.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Simple HTTP server implementation (without external dependencies)
import http.server
import socketserver
import urllib.parse
from http import HTTPStatus

from config import config
from simple_storage import data_store
from main import trading_system
from modules.trading_strategy import get_trading_summary
from modules.stop_loss_monitor import get_stop_loss_status
from utils.logging import get_logger

logger = get_logger(__name__)


class APIHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for the REST API."""
    
    def __init__(self, *args, **kwargs):
        # Suppress default logging
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Override to suppress default logging."""
        pass
    
    def do_GET(self):
        """Handle GET requests."""
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path
            query = urllib.parse.parse_qs(parsed_url.query)
            
            # Route requests
            if path == "/api/status":
                self._handle_status()
            elif path == "/api/news":
                limit = int(query.get('limit', [50])[0])
                self._handle_news(limit)
            elif path == "/api/orders":
                limit = int(query.get('limit', [50])[0])
                self._handle_orders(limit)
            elif path == "/api/positions":
                self._handle_positions()
            elif path == "/api/trading-summary":
                self._handle_trading_summary()
            elif path == "/api/stop-loss-status":
                self._handle_stop_loss_status()
            elif path == "/api/config":
                self._handle_config()
            elif path == "/api/health":
                self._handle_health()
            elif path == "/" or path == "/index.html":
                self._serve_dashboard()
            elif path.startswith("/static/"):
                self._serve_static_file(path)
            else:
                self._send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")
                
        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))
    
    def do_POST(self):
        """Handle POST requests."""
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""
            
            # Route requests
            if path == "/api/system/start":
                self._handle_system_start()
            elif path == "/api/system/stop":
                self._handle_system_stop()
            else:
                self._send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")
                
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))
    
    def _send_json_response(self, data: Any, status: HTTPStatus = HTTPStatus.OK):
        """Send JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response_json = json.dumps(data, default=str, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def _send_error(self, status: HTTPStatus, message: str):
        """Send error response."""
        self._send_json_response({
            'error': message,
            'status': status.value
        }, status)
    
    def _handle_status(self):
        """Handle system status request."""
        status = trading_system.get_system_status()
        self._send_json_response(status)
    
    def _handle_news(self, limit: int):
        """Handle news request."""
        news_items = data_store.get_news_items(limit=limit)
        self._send_json_response({
            'news_items': news_items,
            'total': len(news_items)
        })
    
    def _handle_orders(self, limit: int):
        """Handle orders request."""
        orders = data_store.get_trading_orders(limit=limit)
        self._send_json_response({
            'orders': orders,
            'total': len(orders)
        })
    
    def _handle_positions(self):
        """Handle positions request."""
        open_positions = data_store.get_open_positions()
        all_positions = data_store.get_all_positions(limit=100)
        
        self._send_json_response({
            'open_positions': open_positions,
            'all_positions': all_positions,
            'open_count': len(open_positions),
            'total_count': len(all_positions)
        })
    
    def _handle_trading_summary(self):
        """Handle trading summary request."""
        summary = get_trading_summary()
        self._send_json_response(summary)
    
    def _handle_stop_loss_status(self):
        """Handle stop-loss status request."""
        status = get_stop_loss_status()
        self._send_json_response(status)
    
    def _handle_config(self):
        """Handle configuration request."""
        config_data = {
            'environment': config.environment,
            'binance_testnet': config.binance_testnet,
            'supported_coins': config.supported_coins,
            'trade_amounts': config.trade_amounts,
            'stop_loss_percentage': config.stop_loss_percentage,
            'max_open_positions': config.max_open_positions,
            'max_daily_trades': config.max_daily_trades,
            'daily_loss_limit': config.daily_loss_limit,
            'positive_keywords': config.positive_keywords[:10],  # Sample
            'negative_keywords': config.negative_keywords[:10]   # Sample
        }
        self._send_json_response(config_data)
    
    def _handle_health(self):
        """Handle health check request."""
        self._send_json_response({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })
    
    def _handle_system_start(self):
        """Handle system start request."""
        try:
            if not trading_system.running:
                trading_system.start()
                self._send_json_response({'message': 'System started successfully'})
            else:
                self._send_json_response({'message': 'System is already running'})
        except Exception as e:
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to start system: {e}")
    
    def _handle_system_stop(self):
        """Handle system stop request."""
        try:
            if trading_system.running:
                trading_system.stop()
                self._send_json_response({'message': 'System stopped successfully'})
            else:
                self._send_json_response({'message': 'System is not running'})
        except Exception as e:
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to stop system: {e}")
    
    def _serve_dashboard(self):
        """Serve the main dashboard HTML."""
        html_content = self._get_dashboard_html()
        
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def _serve_static_file(self, path: str):
        """Serve static files (placeholder)."""
        self._send_error(HTTPStatus.NOT_FOUND, "Static files not implemented")
    
    def _get_dashboard_html(self) -> str:
        """Generate dashboard HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Trading System Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; }
        .header h1 { margin-bottom: 10px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h3 { color: #2c3e50; margin-bottom: 15px; }
        .metric { display: flex; justify-content: space-between; margin-bottom: 10px; }
        .metric-label { font-weight: bold; }
        .metric-value { color: #27ae60; }
        .metric-value.negative { color: #e74c3c; }
        .metric-value.neutral { color: #f39c12; }
        .table-container { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }
        .table th { background: #f8f9fa; font-weight: bold; }
        .buttons { margin: 20px 0; }
        .btn { padding: 10px 20px; margin-right: 10px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #3498db; color: white; }
        .btn-danger { background: #e74c3c; color: white; }
        .btn-success { background: #27ae60; color: white; }
        .loading { text-align: center; padding: 20px; color: #666; }
        .error { color: #e74c3c; background: #fdf2f2; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Crypto Trading System Dashboard</h1>
            <p>Real-time monitoring and control for automated cryptocurrency trading</p>
        </div>
        
        <div class="buttons">
            <button class="btn btn-success" onclick="startSystem()">Start System</button>
            <button class="btn btn-danger" onclick="stopSystem()">Stop System</button>
            <button class="btn btn-primary" onclick="refreshData()">Refresh Data</button>
        </div>
        
        <div id="error-container"></div>
        
        <div class="status-grid">
            <div class="card">
                <h3>📊 System Status</h3>
                <div id="system-status" class="loading">Loading...</div>
            </div>
            
            <div class="card">
                <h3>💰 Trading Summary</h3>
                <div id="trading-summary" class="loading">Loading...</div>
            </div>
            
            <div class="card">
                <h3>🔒 Stop-Loss Monitor</h3>
                <div id="stop-loss-status" class="loading">Loading...</div>
            </div>
            
            <div class="card">
                <h3>⚙️ Configuration</h3>
                <div id="config-info" class="loading">Loading...</div>
            </div>
        </div>
        
        <div class="table-container">
            <h3>📰 Recent News</h3>
            <div id="news-table" class="loading">Loading...</div>
        </div>
        
        <div class="table-container">
            <h3>📈 Recent Orders</h3>
            <div id="orders-table" class="loading">Loading...</div>
        </div>
        
        <div class="table-container">
            <h3>💼 Open Positions</h3>
            <div id="positions-table" class="loading">Loading...</div>
        </div>
    </div>

    <script>
        let refreshInterval;
        
        async function fetchAPI(endpoint, options = {}) {
            try {
                const response = await fetch(`/api${endpoint}`, options);
                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }
                return await response.json();
            } catch (error) {
                console.error('API request failed:', error);
                showError(`Failed to fetch ${endpoint}: ${error.message}`);
                throw error;
            }
        }
        
        function showError(message) {
            const container = document.getElementById('error-container');
            container.innerHTML = `<div class="error">${message}</div>`;
            setTimeout(() => container.innerHTML = '', 5000);
        }
        
        function formatCurrency(value) {
            return `$${parseFloat(value).toFixed(2)}`;
        }
        
        function formatDateTime(dateStr) {
            return new Date(dateStr).toLocaleString();
        }
        
        async function loadSystemStatus() {
            try {
                const status = await fetchAPI('/status');
                const html = `
                    <div class="metric">
                        <span class="metric-label">Status:</span>
                        <span class="metric-value ${status.running ? '' : 'negative'}">${status.running ? 'Running' : 'Stopped'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Uptime:</span>
                        <span class="metric-value">${Math.floor(status.uptime_seconds / 60)} minutes</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">News Processed:</span>
                        <span class="metric-value">${status.news_processed}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Environment:</span>
                        <span class="metric-value">${status.config.environment}</span>
                    </div>
                `;
                document.getElementById('system-status').innerHTML = html;
            } catch (error) {
                document.getElementById('system-status').innerHTML = '<div class="error">Failed to load</div>';
            }
        }
        
        async function loadTradingSummary() {
            try {
                const summary = await fetchAPI('/trading-summary');
                const html = `
                    <div class="metric">
                        <span class="metric-label">Total Trades:</span>
                        <span class="metric-value">${summary.total_trades || 0}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Open Positions:</span>
                        <span class="metric-value">${summary.open_positions || 0}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total P&L:</span>
                        <span class="metric-value ${(summary.total_pnl || 0) >= 0 ? '' : 'negative'}">${formatCurrency(summary.total_pnl || 0)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">USDT Balance:</span>
                        <span class="metric-value">${formatCurrency(summary.balances?.USDT || 0)}</span>
                    </div>
                `;
                document.getElementById('trading-summary').innerHTML = html;
            } catch (error) {
                document.getElementById('trading-summary').innerHTML = '<div class="error">Failed to load</div>';
            }
        }
        
        async function loadStopLossStatus() {
            try {
                const status = await fetchAPI('/stop-loss-status');
                const html = `
                    <div class="metric">
                        <span class="metric-label">Active Monitors:</span>
                        <span class="metric-value">${status.total_monitors || 0}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Status:</span>
                        <span class="metric-value ${status.running ? '' : 'negative'}">${status.running ? 'Active' : 'Inactive'}</span>
                    </div>
                `;
                document.getElementById('stop-loss-status').innerHTML = html;
            } catch (error) {
                document.getElementById('stop-loss-status').innerHTML = '<div class="error">Failed to load</div>';
            }
        }
        
        async function loadConfig() {
            try {
                const config = await fetchAPI('/config');
                const html = `
                    <div class="metric">
                        <span class="metric-label">Testnet:</span>
                        <span class="metric-value">${config.binance_testnet ? 'Yes' : 'No'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Stop Loss:</span>
                        <span class="metric-value">${(config.stop_loss_percentage * 100).toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Max Positions:</span>
                        <span class="metric-value">${config.max_open_positions}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Supported Coins:</span>
                        <span class="metric-value">${config.supported_coins.join(', ')}</span>
                    </div>
                `;
                document.getElementById('config-info').innerHTML = html;
            } catch (error) {
                document.getElementById('config-info').innerHTML = '<div class="error">Failed to load</div>';
            }
        }
        
        async function loadNews() {
            try {
                const data = await fetchAPI('/news?limit=10');
                let html = '<table class="table"><thead><tr><th>Time</th><th>Title</th><th>Sentiment</th><th>Coins</th></tr></thead><tbody>';
                
                data.news_items.forEach(news => {
                    const coins = news.mentioned_coins ? JSON.parse(news.mentioned_coins).join(', ') : '';
                    html += `
                        <tr>
                            <td>${formatDateTime(news.created_at)}</td>
                            <td>${news.title.substring(0, 80)}...</td>
                            <td><span class="metric-value ${news.sentiment === 'positive' ? '' : news.sentiment === 'negative' ? 'negative' : 'neutral'}">${news.sentiment}</span></td>
                            <td>${coins}</td>
                        </tr>
                    `;
                });
                
                html += '</tbody></table>';
                document.getElementById('news-table').innerHTML = html;
            } catch (error) {
                document.getElementById('news-table').innerHTML = '<div class="error">Failed to load news</div>';
            }
        }
        
        async function loadOrders() {
            try {
                const data = await fetchAPI('/orders?limit=10');
                let html = '<table class="table"><thead><tr><th>Time</th><th>Symbol</th><th>Side</th><th>Quantity</th><th>Price</th><th>Status</th></tr></thead><tbody>';
                
                data.orders.forEach(order => {
                    html += `
                        <tr>
                            <td>${formatDateTime(order.created_at)}</td>
                            <td>${order.symbol}</td>
                            <td><span class="metric-value ${order.side === 'BUY' ? '' : 'negative'}">${order.side}</span></td>
                            <td>${parseFloat(order.quantity).toFixed(6)}</td>
                            <td>${formatCurrency(order.price)}</td>
                            <td>${order.status}</td>
                        </tr>
                    `;
                });
                
                html += '</tbody></table>';
                document.getElementById('orders-table').innerHTML = html;
            } catch (error) {
                document.getElementById('orders-table').innerHTML = '<div class="error">Failed to load orders</div>';
            }
        }
        
        async function loadPositions() {
            try {
                const data = await fetchAPI('/positions');
                let html = '<table class="table"><thead><tr><th>Symbol</th><th>Quantity</th><th>Entry Price</th><th>Current Price</th><th>P&L</th><th>Status</th></tr></thead><tbody>';
                
                data.open_positions.forEach(position => {
                    const pnl = position.unrealized_pnl || 0;
                    html += `
                        <tr>
                            <td>${position.symbol}</td>
                            <td>${parseFloat(position.quantity).toFixed(6)}</td>
                            <td>${formatCurrency(position.entry_price)}</td>
                            <td>${formatCurrency(position.current_price || position.entry_price)}</td>
                            <td><span class="metric-value ${pnl >= 0 ? '' : 'negative'}">${formatCurrency(pnl)}</span></td>
                            <td>${position.status}</td>
                        </tr>
                    `;
                });
                
                if (data.open_positions.length === 0) {
                    html += '<tr><td colspan="6" style="text-align: center; color: #666;">No open positions</td></tr>';
                }
                
                html += '</tbody></table>';
                document.getElementById('positions-table').innerHTML = html;
            } catch (error) {
                document.getElementById('positions-table').innerHTML = '<div class="error">Failed to load positions</div>';
            }
        }
        
        async function startSystem() {
            try {
                const result = await fetchAPI('/system/start', { method: 'POST' });
                showError('System start requested: ' + result.message);
                setTimeout(refreshData, 2000);
            } catch (error) {
                showError('Failed to start system');
            }
        }
        
        async function stopSystem() {
            try {
                const result = await fetchAPI('/system/stop', { method: 'POST' });
                showError('System stop requested: ' + result.message);
                setTimeout(refreshData, 2000);
            } catch (error) {
                showError('Failed to stop system');
            }
        }
        
        async function refreshData() {
            await Promise.all([
                loadSystemStatus(),
                loadTradingSummary(),
                loadStopLossStatus(),
                loadConfig(),
                loadNews(),
                loadOrders(),
                loadPositions()
            ]);
        }
        
        // Initial load and setup auto-refresh
        document.addEventListener('DOMContentLoaded', () => {
            refreshData();
            refreshInterval = setInterval(refreshData, 30000); // Refresh every 30 seconds
        });
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            if (refreshInterval) clearInterval(refreshInterval);
        });
    </script>
</body>
</html>
        """


class APIServer:
    """Simple HTTP server for the REST API."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
    
    def start(self):
        """Start the API server."""
        try:
            self.server = socketserver.TCPServer((self.host, self.port), APIHandler)
            self.server.allow_reuse_address = True
            
            import threading
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            logger.info(f"API server started at http://{self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            raise
    
    def stop(self):
        """Stop the API server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            
        if self.server_thread:
            self.server_thread.join(timeout=5)
            
        logger.info("API server stopped")


# Global API server instance
api_server = APIServer(host=config.api_host, port=config.api_port)


def start_api_server():
    """Start the API server."""
    api_server.start()


def stop_api_server():
    """Stop the API server."""
    api_server.stop()


if __name__ == "__main__":
    # Run standalone API server
    start_api_server()
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_api_server()