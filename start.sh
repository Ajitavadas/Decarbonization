#!/usr/bin/env bash
set -e

echo "======================================"
echo " Starting Decarbonization Platform"
echo "======================================"
echo

# Start backend
echo ">> Starting backend on http://localhost:8000"
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo ">> Waiting for backend to start..."
for i in {1..30}; do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo ">> Backend is ready!"
    break
  fi
  sleep 1
done

# Start frontend
echo ">> Starting frontend on http://localhost:3000"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo
echo "======================================"
echo " Platform is running!"
echo "======================================"
echo " Backend:  http://localhost:8000"
echo " API Docs: http://localhost:8000/docs"
echo " Frontend: http://localhost:3000"
echo "======================================"
echo
echo "Press Ctrl+C to stop all services"

# Trap Ctrl+C to kill both processes
trap "echo '>> Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

# Wait for any process to exit
wait
