#!/usr/bin/env python
"""
Backend startup script
Run with: uv run backend
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Start the backend server"""
    backend_dir = Path(__file__).parent.parent.parent

    print("=" * 60)
    print("  Starting Backend Server")
    print("=" * 60)
    print()
    print("  API:      http://localhost:8000")
    print("  Docs:     http://localhost:8000/docs")
    print("  Health:   http://localhost:8000/health")
    print()
    print("=" * 60)
    print()

    subprocess.run(
        [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ],
        cwd=str(backend_dir)
    )


if __name__ == "__main__":
    main()
