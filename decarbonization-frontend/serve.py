#!/usr/bin/env python3
"""
Simple HTTP server for the Decarbonization Frontend
Serves static files with CORS enabled for API communication
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 3000

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with CORS support"""
    
    def end_headers(self):
        # Enable CORS for API calls
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.end_headers()

# Change to the frontend directory
os.chdir(Path(__file__).parent)

# Start server
with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║  🌍 Decarbonization Dashboard Server                      ║
    ╠═══════════════════════════════════════════════════════════╣
    ║                                                           ║
    ║  Dashboard:  http://localhost:{PORT}                         ║
    ║  Backend API: http://localhost:8000                       ║
    ║                                                           ║
    ║  Press Ctrl+C to stop the server                          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
        httpd.shutdown()
