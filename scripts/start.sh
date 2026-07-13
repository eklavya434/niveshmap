#!/bin/bash
set -e

echo "=== Starting FastAPI Spatial API server in the background ==="
# Export python path
export PYTHONPATH="."
python api_server.py &
API_PID=$!

echo "=== Verifying FastAPI backend startup ==="
python -c "
import urllib.request
import json
import time
import sys

for i in range(30):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=1) as r:
            data = json.loads(r.read().decode())
            if data.get('status') == 'ok':
                print('FastAPI backend is online and healthy.')
                sys.exit(0)
    except Exception as e:
        pass
    print(f'Waiting for backend... ({i+1}/30)')
    time.sleep(1)

print('Error: FastAPI backend failed to start or become healthy.')
sys.exit(1)
"

echo "=== Starting Streamlit public demo on port 7860 ==="
# Run streamlit on port 7860, headless, binding to all interfaces
exec streamlit run app.py --server.port 7860 --server.address 0.0.0.0 --server.headless true
