"""Run the NiveshMap spatial HTTP adapter.

Usage:
    python api_server.py
    uvicorn api_server:app --host 0.0.0.0 --port 8000
"""

from src.ncr_intelligence.api import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
