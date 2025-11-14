#!/usr/bin/env bash

set -euo pipefail

# Config
NAMESPACE="secondnature-alpha"
SERVICE_NAME="secondnature-alpha-db"
LOCAL_PORT="5432"
REMOTE_PORT="5432"
PG_URL="postgresql://postgres:postgres@127.0.0.1:${LOCAL_PORT}/default?sslmode=disable"

cleanup() {
  if [[ -n "${PF_PID:-}" ]] && ps -p "$PF_PID" >/dev/null 2>&1; then
    echo "Stopping port-forward (pid $PF_PID)..."
    kill "$PF_PID" >/dev/null 2>&1 || true
    wait "$PF_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT

echo "Starting kubectl port-forward ${SERVICE_NAME} ${LOCAL_PORT}:${REMOTE_PORT} -n ${NAMESPACE}..."
kubectl port-forward svc/${SERVICE_NAME} ${LOCAL_PORT}:${REMOTE_PORT} -n ${NAMESPACE} >/dev/null 2>&1 &
PF_PID=$!

# Wait for port to be ready
echo "Waiting for Postgres to accept connections on 127.0.0.1:${LOCAL_PORT}..."
for i in {1..60}; do
  if nc -z 127.0.0.1 "${LOCAL_PORT}" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! nc -z 127.0.0.1 "${LOCAL_PORT}" >/dev/null 2>&1; then
  echo "Failed to connect to Postgres on 127.0.0.1:${LOCAL_PORT}. Exiting."
  exit 1
fi

export PG_DATABASE_URL="${PG_URL}"
echo "PG_DATABASE_URL set for this process."

echo "Running sync-all to prod..."
python -m src.cli sync-all "$@"

echo "Done."

