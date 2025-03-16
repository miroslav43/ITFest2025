#!/bin/bash

# Start the backend server
echo "Starting the backend server..."
cd chat_backend
python -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait a moment for the backend to initialize
sleep 2

# Start the frontend development server
echo "Starting the frontend development server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Function to handle script termination
cleanup() {
  echo "Shutting down servers..."
  kill $BACKEND_PID
  kill $FRONTEND_PID
  exit 0
}

# Set up trap to catch termination signals
trap cleanup SIGINT SIGTERM

# Keep the script running
echo "Both servers are running. Press Ctrl+C to stop."
wait