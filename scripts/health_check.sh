#!/bin/bash

# System Health Check Script
# Monitors system health and provides status reports

echo "🏥 Crypto Trading System Health Check"
echo "===================================="

# Check if system is running
check_system_running() {
    if [[ -f "logs/system.pid" ]]; then
        PID=$(cat logs/system.pid)
        if kill -0 $PID 2>/dev/null; then
            echo "✅ System Status: RUNNING (PID: $PID)"
            return 0
        else
            echo "❌ System Status: NOT RUNNING (stale PID file)"
            rm -f logs/system.pid
            return 1
        fi
    else
        # Check for any running processes
        PIDS=$(pgrep -f "python.*main.py" || true)
        if [[ -n "$PIDS" ]]; then
            echo "⚠️  System Status: RUNNING (no PID file, processes: $PIDS)"
            return 0
        else
            echo "❌ System Status: NOT RUNNING"
            return 1
        fi
    fi
}

# Check API server connectivity
check_api_server() {
    local HOST=${API_HOST:-127.0.0.1}
    local PORT=${API_PORT:-8000}
    
    if curl -s -f "http://$HOST:$PORT/api/health" > /dev/null 2>&1; then
        echo "✅ API Server: ACCESSIBLE (http://$HOST:$PORT)"
        
        # Get system status from API
        STATUS=$(curl -s "http://$HOST:$PORT/api/status" 2>/dev/null || echo "{}")
        if [[ "$STATUS" != "{}" ]]; then
            UPTIME=$(echo "$STATUS" | python -c "import sys, json; data=json.load(sys.stdin); print(f\"{data.get('uptime_seconds', 0) // 60} minutes\")" 2>/dev/null || echo "unknown")
            NEWS_COUNT=$(echo "$STATUS" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('news_processed', 0))" 2>/dev/null || echo "unknown")
            echo "📊 Uptime: $UPTIME"
            echo "📰 News Processed: $NEWS_COUNT"
        fi
    else
        echo "❌ API Server: NOT ACCESSIBLE"
    fi
}

# Check data files
check_data_files() {
    local DATA_DIR="data"
    
    if [[ -d "$DATA_DIR" ]]; then
        echo "✅ Data Directory: EXISTS"
        
        # Check individual data files
        local files=("news_items.json" "trading_orders.json" "positions.json" "system_metrics.json")
        for file in "${files[@]}"; do
            if [[ -f "$DATA_DIR/$file" ]]; then
                local size=$(stat -f%z "$DATA_DIR/$file" 2>/dev/null || stat -c%s "$DATA_DIR/$file" 2>/dev/null || echo "0")
                echo "   📄 $file: EXISTS (${size} bytes)"
            else
                echo "   ❌ $file: MISSING"
            fi
        done
    else
        echo "❌ Data Directory: MISSING"
    fi
}

# Check log files
check_log_files() {
    local LOG_FILE=${LOG_FILE:-crypto_trading.log}
    
    if [[ -f "$LOG_FILE" ]]; then
        local size=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo "0")
        local lines=$(wc -l < "$LOG_FILE" 2>/dev/null || echo "0")
        echo "✅ Main Log: EXISTS (${size} bytes, ${lines} lines)"
        
        # Check for recent errors
        local errors=$(tail -100 "$LOG_FILE" 2>/dev/null | grep -i error | wc -l || echo "0")
        if [[ "$errors" -gt 0 ]]; then
            echo "⚠️  Recent Errors: $errors (check log file)"
        else
            echo "✅ Recent Errors: None"
        fi
    else
        echo "❌ Main Log: NOT FOUND"
    fi
    
    if [[ -d "logs" ]]; then
        echo "✅ Logs Directory: EXISTS"
    else
        echo "❌ Logs Directory: MISSING"
    fi
}

# Check configuration
check_configuration() {
    if [[ -f ".env" ]]; then
        echo "✅ Configuration: .env file found"
        
        # Check critical settings
        source .env 2>/dev/null || true
        
        if [[ "$BINANCE_API_KEY" == "your_api_key_here" ]] || [[ -z "$BINANCE_API_KEY" ]]; then
            echo "⚠️  Binance API Key: NOT CONFIGURED"
        else
            echo "✅ Binance API Key: CONFIGURED"
        fi
        
        echo "🔧 Environment: ${ENVIRONMENT:-development}"
        echo "🧪 Testnet Mode: ${BINANCE_TESTNET:-true}"
    else
        echo "❌ Configuration: .env file missing"
    fi
}

# Check disk space
check_disk_space() {
    local available=$(df . | tail -1 | awk '{print $4}')
    local available_mb=$((available / 1024))
    
    if [[ "$available_mb" -gt 1000 ]]; then
        echo "✅ Disk Space: ${available_mb}MB available"
    elif [[ "$available_mb" -gt 100 ]]; then
        echo "⚠️  Disk Space: ${available_mb}MB available (getting low)"
    else
        echo "❌ Disk Space: ${available_mb}MB available (critically low)"
    fi
}

# Check memory usage
check_memory_usage() {
    if command -v python >/dev/null; then
        local mem_usage=$(python -c "
import psutil
import os
try:
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    print(f'{mem_info.rss / 1024 / 1024:.1f}MB')
except:
    print('unknown')
" 2>/dev/null || echo "unknown")
        echo "📊 Memory Usage: $mem_usage"
    fi
}

# Perform all checks
main() {
    echo "🕒 Check Time: $(date)"
    echo ""
    
    echo "🔍 System Process Check:"
    if check_system_running; then
        SYSTEM_RUNNING=true
    else
        SYSTEM_RUNNING=false
    fi
    echo ""
    
    echo "🌐 API Server Check:"
    if [[ "$SYSTEM_RUNNING" == "true" ]]; then
        check_api_server
    else
        echo "❌ Skipped (system not running)"
    fi
    echo ""
    
    echo "💾 Data Files Check:"
    check_data_files
    echo ""
    
    echo "📝 Log Files Check:"
    check_log_files
    echo ""
    
    echo "⚙️  Configuration Check:"
    check_configuration
    echo ""
    
    echo "💿 System Resources:"
    check_disk_space
    check_memory_usage
    echo ""
    
    # Overall health summary
    echo "📋 Health Summary:"
    if [[ "$SYSTEM_RUNNING" == "true" ]]; then
        echo "✅ Overall Status: HEALTHY"
        echo "💡 System is running and operational"
    else
        echo "⚠️  Overall Status: SYSTEM DOWN"
        echo "💡 Use './scripts/start_system.sh' to start the system"
    fi
}

# Run health check
main "$@"