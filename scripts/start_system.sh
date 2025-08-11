#!/bin/bash

# Crypto Trading System Startup Script
# This script handles system initialization and startup

set -e

echo "🚀 Starting Crypto Trading System..."
echo "================================="

# Check Python version
python_version=$(python --version 2>&1)
echo "Python version: $python_version"

# Check if we're in the correct directory
if [[ ! -f "main.py" ]]; then
    echo "❌ Error: main.py not found. Please run this script from the project root directory."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data
mkdir -p logs

# Check for configuration file
if [[ ! -f ".env" ]]; then
    echo "⚠️  Warning: .env file not found. Creating sample configuration..."
    cat > .env << EOF
# Environment Configuration
ENVIRONMENT=development
DEBUG=true

# Binance API Configuration (REPLACE WITH YOUR VALUES)
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
EOF
    echo "📝 Sample .env file created. Please edit it with your configuration."
fi

# Check if running in development or production mode
ENVIRONMENT=${ENVIRONMENT:-development}
echo "🔧 Environment: $ENVIRONMENT"

if [[ "$ENVIRONMENT" == "production" ]]; then
    echo "🏭 Production mode - enabling additional safety checks..."
    
    # Check for required environment variables
    if [[ -z "$BINANCE_API_KEY" ]] || [[ "$BINANCE_API_KEY" == "your_api_key_here" ]]; then
        echo "❌ Error: BINANCE_API_KEY not set for production"
        exit 1
    fi
    
    if [[ -z "$BINANCE_API_SECRET" ]] || [[ "$BINANCE_API_SECRET" == "your_api_secret_here" ]]; then
        echo "❌ Error: BINANCE_API_SECRET not set for production"
        exit 1
    fi
    
    echo "⚠️  WARNING: Running in PRODUCTION mode with real trading!"
    echo "Press Ctrl+C within 10 seconds to cancel..."
    sleep 10
fi

# Run system health check
echo "🏥 Running system health check..."
python -c "
import sys
sys.path.append('.')
try:
    from config import config
    from simple_storage import data_store
    print('✅ Configuration loaded successfully')
    print('✅ Data storage initialized')
    print('🎯 System health check passed')
except Exception as e:
    print(f'❌ Health check failed: {e}')
    sys.exit(1)
"

if [[ $? -ne 0 ]]; then
    echo "❌ System health check failed. Please check your configuration."
    exit 1
fi

# Start the system
echo "🚀 Starting trading system..."
echo "Dashboard will be available at: http://127.0.0.1:8000"
echo "Press Ctrl+C to stop the system"
echo ""

# Start with process monitoring
if [[ "$1" == "--daemon" ]]; then
    echo "🔄 Starting in daemon mode..."
    nohup python main.py > logs/system.log 2>&1 &
    echo $! > logs/system.pid
    echo "✅ System started with PID $(cat logs/system.pid)"
    echo "📊 Web dashboard: http://127.0.0.1:8000"
    echo "📝 Logs: tail -f logs/system.log"
else
    exec python main.py
fi