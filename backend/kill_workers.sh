#!/bin/bash
# Kill all CodeNova worker processes

echo "Stopping all CodeNova workers..."

# Kill hybrid workers
pkill -f "hybrid_worker" && echo "✓ Killed hybrid workers"

# Kill forwarders
pkill -f "hybrid_forwarder" && echo "✓ Killed forwarders"

# Kill any Python processes running backend tasks
pkill -f "app.core.hybrid" && echo "✓ Killed remaining task processes"

# Kill main app if running
pkill -f "app.main" && echo "✓ Killed main app"

echo "All workers stopped!"
