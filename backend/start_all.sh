#!/bin/bash
# Start all CodeNova queue services

echo "Starting CodeNova Hybrid Queue System..."
echo "========================================="

# Kill any existing processes
echo "Cleaning up old processes..."
pkill -f "hybrid_forwarder" 2>/dev/null
pkill -f "hybrid_worker" 2>/dev/null
pkill -f "start_hybrid_queue" 2>/dev/null

sleep 2

# Start the hybrid queue system (both forwarder and worker)
echo "Starting forwarder and worker..."
python start_hybrid_queue.py --mode both

echo "Hybrid queue system stopped."
