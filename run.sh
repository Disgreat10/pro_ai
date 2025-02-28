#!/bin/bash

# Kill any existing processes using port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Install websockets package if not already installed
pip install websockets --quiet

# Install required packages
pip install daphne --quiet
pip install channels --quiet
pip install channels_redis --quiet

# Set Django settings module
export DJANGO_SETTINGS_MODULE=blackbox_trader.settings

# Start Daphne ASGI server
cd /project/sandbox/user-workspace/pro_ai && daphne -b 0.0.0.0 -p 8000 blackbox_trader.asgi:application &
DAPHNE_PID=$!

# Start MCX market data feed with verbose output
python manage.py mcx_feed --verbose &
MCX_PID=$!

# Function to handle script termination
cleanup() {
    echo "Stopping services..."
    kill $DAPHNE_PID 2>/dev/null
    kill $MCX_PID 2>/dev/null
    exit 0
}

# Register cleanup function for script termination
trap cleanup SIGINT SIGTERM

echo "Services started:"
echo "1. Daphne ASGI server (PID: $DAPHNE_PID)"
echo "2. MCX Feed (PID: $MCX_PID)"
echo "Press Ctrl+C to stop all services"

# Wait for both processes
wait $DAPHNE_PID $MCX_PID
