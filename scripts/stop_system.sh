#!/bin/bash

# Crypto Trading System Stop Script
# Gracefully stops the trading system

echo "🛑 Stopping Crypto Trading System..."

# Check for PID file
if [[ -f "logs/system.pid" ]]; then
    PID=$(cat logs/system.pid)
    echo "📍 Found PID file with process ID: $PID"
    
    if kill -0 $PID 2>/dev/null; then
        echo "⏹️  Sending SIGTERM to process $PID..."
        kill -TERM $PID
        
        # Wait for graceful shutdown
        echo "⏳ Waiting for graceful shutdown..."
        for i in {1..30}; do
            if ! kill -0 $PID 2>/dev/null; then
                echo "✅ Process stopped gracefully"
                rm -f logs/system.pid
                exit 0
            fi
            sleep 1
        done
        
        # Force kill if necessary
        echo "⚠️  Graceful shutdown timeout, forcing termination..."
        kill -KILL $PID 2>/dev/null
        rm -f logs/system.pid
        echo "💀 Process forcefully terminated"
    else
        echo "❌ Process $PID not running, removing stale PID file"
        rm -f logs/system.pid
    fi
else
    echo "❓ No PID file found, checking for running processes..."
    
    # Look for running Python processes with main.py
    PIDS=$(pgrep -f "python.*main.py" || true)
    if [[ -n "$PIDS" ]]; then
        echo "🔍 Found trading system processes: $PIDS"
        echo "🛑 Stopping processes..."
        echo "$PIDS" | xargs kill -TERM
        sleep 2
        
        # Check if any are still running
        REMAINING=$(pgrep -f "python.*main.py" || true)
        if [[ -n "$REMAINING" ]]; then
            echo "⚠️  Some processes still running, force killing..."
            echo "$REMAINING" | xargs kill -KILL
        fi
        echo "✅ All processes stopped"
    else
        echo "❓ No trading system processes found"
    fi
fi

echo "🏁 System shutdown complete"