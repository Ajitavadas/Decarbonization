#!/usr/bin/env python
"""
Frontend startup script
Run with: uv run frontend
"""

import subprocess
import sys
import os
from pathlib import Path


def main():
    """Start the frontend dev server"""
    project_root = Path(__file__).parent.parent.parent.parent
    frontend_dir = project_root / "frontend"
    node_env_dir = project_root / ".nodeenv"

    print("=" * 60)
    print("  Starting Frontend Server")
    print("=" * 60)
    print()

    # Check if Node.js environment exists
    if not node_env_dir.exists():
        print(">> Setting up Node.js environment (first time only)...")
        print("   This may take 2-3 minutes...")
        subprocess.run(
            [sys.executable, "-m", "nodeenv", "--node=20.11.0", str(node_env_dir)],
            check=True
        )
        print(">> Node.js environment created!")
        print()

    # Get npm executable path
    if os.name == 'nt':  # Windows
        npm_bin = node_env_dir / "Scripts" / "npm"
        node_bin = node_env_dir / "Scripts" / "node.exe"
    else:  # Unix-like
        npm_bin = node_env_dir / "bin" / "npm"
        node_bin = node_env_dir / "bin" / "node"

    # Verify npm exists
    if not npm_bin.exists():
        print(f"ERROR: npm not found at {npm_bin}")
        print("Please run: cd backend && uv run python -m nodeenv --node=20.11.0 --prebuilt ../.nodeenv")
        sys.exit(1)

    # Check if node_modules exists
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print(">> Installing frontend dependencies...")
        print("   This may take 2-3 minutes...")
        subprocess.run(
            [str(npm_bin), "install"],
            cwd=str(frontend_dir),
            check=True
        )
        print(">> Dependencies installed!")
        print()

    print("  Frontend:  http://localhost:3000")
    print()
    print("=" * 60)
    print()

    # Start frontend dev server
    subprocess.run(
        [str(npm_bin), "run", "dev"],
        cwd=str(frontend_dir)
    )


if __name__ == "__main__":
    main()
