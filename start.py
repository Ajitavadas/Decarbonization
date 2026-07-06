#!/usr/bin/env python
"""
Unified startup script for the Decarbonization Platform
Run with: cd backend && uv run python ../start.py
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path


class PlatformManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.node_env_dir = self.project_root / ".nodeenv"
        self.processes = []

    def print_banner(self):
        print("=" * 60)
        print("  Decarbonization Platform - Unified Startup")
        print("=" * 60)
        print()

    def setup_node_environment(self):
        """Setup Node.js environment using nodeenv"""
        if self.node_env_dir.exists():
            print(">> Node.js environment already exists")
            return

        print(">> Setting up Node.js environment (first time only)...")
        print("   This may take 2-3 minutes...")
        try:
            subprocess.run(
                [sys.executable, "-m", "nodeenv", "--node=20.11.0", str(self.node_env_dir)],
                check=True,
                cwd=str(self.project_root)
            )
            print(">> Node.js environment created successfully")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to create Node.js environment: {e}")
            sys.exit(1)

    def get_node_binaries(self):
        """Get paths to node and npm binaries"""
        if os.name == 'nt':  # Windows
            node_bin = self.node_env_dir / "Scripts" / "node.exe"
            npm_bin = self.node_env_dir / "Scripts" / "npm.cmd"
        else:  # Unix-like
            node_bin = self.node_env_dir / "bin" / "node"
            npm_bin = self.node_env_dir / "bin" / "npm"
        return node_bin, npm_bin

    def install_frontend_deps(self):
        """Install frontend dependencies"""
        node_modules = self.frontend_dir / "node_modules"
        if node_modules.exists():
            print(">> Frontend dependencies already installed")
            return

        print(">> Installing frontend dependencies...")
        print("   This may take 2-3 minutes...")
        _, npm_bin = self.get_node_binaries()

        try:
            subprocess.run(
                [str(npm_bin), "install"],
                check=True,
                cwd=str(self.frontend_dir)
            )
            print(">> Frontend dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to install frontend dependencies: {e}")
            sys.exit(1)

    def start_backend(self):
        """Start the backend server"""
        print(">> Starting backend on http://localhost:8000")
        backend_process = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ],
            cwd=str(self.backend_dir)
        )
        self.processes.append(("backend", backend_process))

        # Wait for backend to be ready
        print(">> Waiting for backend to start...")
        for i in range(30):
            try:
                import httpx
                response = httpx.get("http://localhost:8000/health", timeout=1.0)
                if response.status_code == 200:
                    print(">> Backend is ready!")
                    break
            except:
                time.sleep(1)
        else:
            print("WARNING: Backend may not be ready yet")

    def start_frontend(self):
        """Start the frontend dev server"""
        print(">> Starting frontend on http://localhost:3000")
        _, npm_bin = self.get_node_binaries()

        frontend_process = subprocess.Popen(
            [str(npm_bin), "run", "dev"],
            cwd=str(self.frontend_dir)
        )
        self.processes.append(("frontend", frontend_process))
        time.sleep(2)

    def print_urls(self):
        """Print access URLs"""
        print()
        print("=" * 60)
        print("  Platform is Running!")
        print("=" * 60)
        print(" Backend:  http://localhost:8000")
        print(" API Docs: http://localhost:8000/docs")
        print(" Frontend: http://localhost:3000")
        print("=" * 60)
        print()
        print("Press Ctrl+C to stop all services")
        print()

    def cleanup(self, signum=None, frame=None):
        """Stop all processes"""
        print("\n>> Stopping services...")
        for name, process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f">> {name} stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f">> {name} killed")
            except:
                pass
        sys.exit(0)

    def run(self):
        """Main run method"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

        self.print_banner()

        # Setup Node.js environment
        self.setup_node_environment()

        # Install frontend dependencies
        self.install_frontend_deps()

        # Start services
        self.start_backend()
        self.start_frontend()

        # Print access URLs
        self.print_urls()

        # Wait for processes
        try:
            while True:
                for name, process in self.processes:
                    if process.poll() is not None:
                        print(f"ERROR: {name} process exited unexpectedly")
                        self.cleanup()
                time.sleep(1)
        except KeyboardInterrupt:
            self.cleanup()


if __name__ == "__main__":
    manager = PlatformManager()
    manager.run()
