#!/usr/bin/env bash
# Convenience script: starts Mosquitto and prints the commands to run the
# ROS 2 sim, backend, and dashboard in separate terminals.
set -e
cd "$(dirname "$0")/.."

docker compose up -d
echo "Mosquitto is up on localhost:1883."
echo
echo "In separate terminals, run:"
echo "  source .venv/bin/activate && python -m ros2_sim.fake_robot --rate 10"
echo "  source .venv/bin/activate && uvicorn backend.app:app --reload"
echo "  open dashboard/index.html"
