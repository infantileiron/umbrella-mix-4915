#!/bin/sh
set -eu
if [ "${SEED_DEMO:-true}" = true ]; then
  python -m scripts.seed_demo || printf 'Demo seed failed. Run python -m scripts.seed_demo to retry.\n' >&2
fi
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
