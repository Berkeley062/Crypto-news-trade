# Crypto News-Driven Automatic Trading System

A comprehensive cryptocurrency trading system that automatically analyzes news sentiment and executes trades based on market sentiment analysis.

## 🚀 Features

### Core Functionality
- **Real-time News Collection**: Collects cryptocurrency news from multiple sources
- **Sentiment Analysis**: Advanced NLP-based sentiment analysis with keyword matching
- **Automated Trading**: Executes buy/sell orders based on sentiment signals
- **Risk Management**: Built-in stop-loss monitoring and position management
- **Web Dashboard**: Real-time monitoring interface with comprehensive analytics

### Technical Capabilities
- **Multi-source News Aggregation**: WebSocket and REST API news collection
- **Sentiment Processing Pipeline**: Keyword-based and lexicon analysis methods
- **Exchange Integration**: Binance API integration (testnet/mainnet support)
- **Position Monitoring**: Automatic stop-loss execution and P&L tracking
- **Configuration Management**: Environment-based configuration system
- **Comprehensive Logging**: Multi-level logging with file rotation

## 📋 System Requirements

### Minimum Requirements
- Python 3.8+
- 1GB RAM
- 1GB available disk space
- Internet connection for news feeds and trading

### Recommended Requirements
- Python 3.10+
- 2GB RAM
- 5GB available disk space
- Stable internet connection (low latency for trading)

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/Berkeley062/Crypto-news-trade.git
cd Crypto-news-trade
```

### 2. Install Dependencies
```bash
# Option 1: Install from requirements.txt (when dependencies are available)
pip install -r requirements.txt

# Option 2: Manual installation of core packages
pip install fastapi uvicorn sqlalchemy pydantic websocket-client
```

### 3. Configuration Setup
Create a `.env` file in the project root:

```env
# Environment Configuration
ENVIRONMENT=development
DEBUG=true

# Binance API Configuration
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
BINANCE_TESTNET=true

# Trading Parameters
STOP_LOSS_PERCENTAGE=0.1
TRADE_AMOUNT_USDT=10.0
MAX_OPEN_POSITIONS=5
MAX_DAILY_TRADES=20
DAILY_LOSS_LIMIT=100.0

# API Server Configuration
API_HOST=127.0.0.1
API_PORT=8000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=crypto_trading.log
```

## 🚀 Quick Start

### 1. Basic System Start
```bash
# Start the complete trading system
python main.py
```

### 2. Web Dashboard Only
```bash
# Start just the web interface
python api.py
```

### 3. Run Tests
```bash
# Execute the test suite
python tests/test_system.py
```

## 📊 Web Dashboard

Access the web dashboard at: `http://localhost:8000`

### Dashboard Features
- **System Status**: Real-time system health and uptime monitoring
- **Trading Summary**: P&L, open positions, and trading statistics
- **News Feed**: Latest processed news with sentiment analysis
- **Order History**: Complete trading order history
- **Position Monitoring**: Active positions with stop-loss status
- **Configuration View**: Current system settings and parameters

### API Endpoints
- `GET /api/status` - System status information
- `GET /api/news` - Recent news items with sentiment analysis
- `GET /api/orders` - Trading order history
- `GET /api/positions` - Position information
- `GET /api/trading-summary` - Trading performance summary
- `POST /api/system/start` - Start the trading system
- `POST /api/system/stop` - Stop the trading system

## 🔧 Configuration Options

### Trading Parameters
```python
# Core trading settings
STOP_LOSS_PERCENTAGE = 0.1        # 10% stop loss
TRADE_AMOUNT_USDT = 10.0          # Default trade size
MAX_OPEN_POSITIONS = 5            # Maximum concurrent positions
MAX_DAILY_TRADES = 20             # Daily trade limit
DAILY_LOSS_LIMIT = 100.0          # Daily loss threshold

# Supported trading pairs
SUPPORTED_COINS = ["BTC", "ETH", "BNB", "ADA", "SOL"]

# Individual trade amounts per symbol
TRADE_AMOUNTS = {
    "BTCUSDT": 10.0,
    "ETHUSDT": 10.0,
    "BNBUSDT": 10.0,
    "ADAUSDT": 10.0,
    "SOLUSDT": 10.0
}
```

### Sentiment Analysis Keywords
```python
# Positive sentiment keywords
POSITIVE_KEYWORDS = [
    "bullish", "moon", "pump", "rally", "partnership", "adoption",
    "breakthrough", "upgrade", "integration", "listing", "launch"
]

# Negative sentiment keywords  
NEGATIVE_KEYWORDS = [
    "bearish", "dump", "crash", "hack", "scam", "regulation", "ban",
    "lawsuit", "shutdown", "bankruptcy", "exploit", "vulnerability"
]
```

## 🏗️ Architecture Overview

### System Components
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  News Collector │───▶│ Sentiment Analyzer│───▶│ Trading Strategy│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Storage  │    │   Configuration  │    │ Binance Client  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                   ┌─────────────────────────┐
                   │   Stop-Loss Monitor     │
                   └─────────────────────────┘
                                 │
                                 ▼
                   ┌─────────────────────────┐
                   │     Web Dashboard       │
                   └─────────────────────────┘
```

### Module Descriptions

#### News Collection Module (`modules/news_collector.py`)
- **Mock News Collector**: Generates realistic test news for development
- **REST API Collector**: Framework for real news API integration
- **WebSocket Collector**: Real-time news feed processing (extensible)

#### Sentiment Analysis Module (`modules/sentiment_analyzer.py`)
- **Keyword Analysis**: Rule-based sentiment detection using predefined keywords
- **Lexicon Analysis**: Dictionary-based sentiment scoring
- **Combined Analysis**: Hybrid approach for improved accuracy
- **Cryptocurrency Detection**: Automatic coin symbol extraction

#### Trading Strategy Module (`modules/trading_strategy.py`)
- **Signal Generation**: Creates buy/sell signals based on sentiment
- **Risk Management**: Enforces trading limits and safety checks
- **Position Management**: Tracks open positions and P&L
- **Trade Execution**: Coordinates with Binance API for order placement

#### Binance Client Module (`modules/binance_client.py`)
- **Mock Client**: Simulated trading for development/testing
- **API Wrapper**: Abstraction layer for real Binance API integration
- **Order Management**: Create, monitor, and cancel trading orders
- **Account Management**: Balance checking and position tracking

#### Stop-Loss Monitor (`modules/stop_loss_monitor.py`)
- **Position Monitoring**: Real-time price tracking for open positions
- **Automatic Execution**: Triggers stop-loss orders when thresholds are met
- **Threading Management**: Concurrent monitoring of multiple positions
- **Risk Protection**: Prevents excessive losses through automated selling

## 🧪 Testing

### Test Suite Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow validation
- **Mock Testing**: Simulated trading without real API calls
- **Data Storage Tests**: Database operations and data integrity
- **Sentiment Analysis Tests**: Algorithm accuracy verification

### Running Tests
```bash
# Run all tests
python tests/test_system.py

# Run specific test categories
python -m unittest tests.test_system.TestSentimentAnalyzer
python -m unittest tests.test_system.TestTradingStrategy
python -m unittest tests.test_system.TestMockBinanceClient
```

## 🔒 Security Considerations

### API Key Management
- Store API keys in environment variables, never in code
- Use testnet for development and testing
- Implement API key rotation for production use
- Monitor API usage and rate limits

### Risk Management
- Always use stop-loss orders to limit potential losses
- Set appropriate position size limits
- Implement daily loss limits
- Monitor system performance continuously

### Data Security
- Encrypt sensitive configuration data
- Use secure connections for all API communications
- Implement proper logging without exposing secrets
- Regular security audits and updates

## 🚀 Deployment

### Development Deployment
```bash
# Start development server with hot reload
python main.py
```

### Production Deployment
```bash
# Set production environment
export ENVIRONMENT=production
export DEBUG=false
export BINANCE_TESTNET=false

# Start production server
nohup python main.py > trading_system.log 2>&1 &
```

### Docker Deployment (Future Enhancement)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

## 📈 Monitoring and Maintenance

### System Health Checks
- Monitor system uptime and performance
- Track trading success rate and P&L
- Monitor news processing pipeline
- Check API connectivity and rate limits

### Log Management
- Logs are written to `crypto_trading.log`
- Automatic log rotation prevents disk space issues
- Different log levels for development vs production
- Error tracking and alerting capabilities

### Performance Optimization
- Monitor memory usage for long-running processes
- Optimize database queries and storage
- Tune sentiment analysis performance
- Adjust trading frequency based on market conditions

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Ensure all tests pass
5. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Include comprehensive docstrings
- Write unit tests for new features
- Maintain backward compatibility

## ⚠️ Disclaimer

This software is for educational and research purposes. Cryptocurrency trading involves significant financial risk. Users should:

- Thoroughly test on testnet before live trading
- Never trade with funds they cannot afford to lose
- Understand the risks of automated trading
- Comply with all applicable laws and regulations
- Seek professional financial advice when appropriate

## 📄 License

This project is open source and available under the MIT License.

## 📞 Support

For support, questions, or contributions:
- Create an issue in the GitHub repository
- Review the documentation and code comments
- Check the test suite for usage examples
- Join the community discussions