#!/bin/bash
# Restart the queue system with a clean slate

echo "========================================="
echo "CodeNova Queue System - Fresh Restart"
echo "========================================="

# Stop all workers
echo ""
echo "1. Stopping all workers..."
pkill -f "hybrid_forwarder" 2>/dev/null && echo "   ✓ Stopped forwarder"
pkill -f "hybrid_worker" 2>/dev/null && echo "   ✓ Stopped worker"
pkill -f "start_hybrid_queue" 2>/dev/null && echo "   ✓ Stopped queue manager"

sleep 2

# Clear the queue
echo ""
echo "2. Clearing queue..."
echo "yes" | python clear_queue.py

# Start fresh
echo ""
echo "3. Starting queue system..."
python start_hybrid_queue.py --mode both
