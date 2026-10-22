#!/usr/bin/env bash
# Launches the whole pipeline -- Mosquitto, the ROS 2 sim, and the backend --
# and opens the live logs page. Ctrl+C stops the ROS 2 sim and backend
# (Mosquitto is left running since it's shared infra).
#
# The ROS 2 sim (ros2_sim.fake_robot) replaced the old synthetic
# generator/external_emulator as the data source: it publishes real
# ROS 2 message shapes, and backend/ros2_translate.py maps them onto the
# dashboard's point schema. There's no scenario/fault-injection switch
# anymore -- that was generator.main-only and has no ROS 2 equivalent.
set -e
cd "$(dirname "$0")/.."

RATE="${1:-10}"

mkdir -p logs
source .venv/bin/activate

docker compose up -d
echo "[run_all] Mosquitto is up on localhost:1883."

BACKEND_PID=""
ROS2SIM_PID=""

if lsof -i :8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[run_all] something is already listening on :8000 -- assuming the backend is running, not starting another one."
else
  uvicorn backend.app:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
  BACKEND_PID=$!
  echo "[run_all] backend started (pid $BACKEND_PID), logging to logs/backend.log"
fi

if pgrep -f "generator.main" >/dev/null 2>&1; then
  echo "[run_all] WARNING: a generator.main process is still running -- it publishes under rover/# too and will double-feed the backend alongside ros2_sim. Kill it (pkill -f generator.main) if you don't want that."
fi

if pgrep -f "ros2_sim.fake_robot" >/dev/null 2>&1; then
  echo "[run_all] a ros2_sim.fake_robot process is already running -- not starting another one."
else
  python -m ros2_sim.fake_robot --rate "$RATE" > logs/ros2_sim.log 2>&1 &
  ROS2SIM_PID=$!
  echo "[run_all] ros2_sim started (pid $ROS2SIM_PID, rate=${RATE}Hz), logging to logs/ros2_sim.log"
fi

cleanup() {
  echo
  echo "[run_all] shutting down..."
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
  [ -n "$ROS2SIM_PID" ] && kill "$ROS2SIM_PID" 2>/dev/null
  echo "[run_all] Mosquitto left running (docker compose down to stop it)."
}
trap cleanup EXIT INT TERM

sleep 1
echo "[run_all] opening dashboard + logs page..."
open dashboard/index.html 2>/dev/null || true
open dashboard/logs.html 2>/dev/null || true

echo "[run_all] tailing logs -- Ctrl+C to stop ros2_sim + backend (Mosquitto stays up)."
echo
tail -f logs/backend.log logs/ros2_sim.log
