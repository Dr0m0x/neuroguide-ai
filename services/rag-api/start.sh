#!/bin/bash
set -e
cd "$(dirname "$0")"
pip install -r requirements.txt -q
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-5001}" --reload
