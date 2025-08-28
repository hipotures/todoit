#!/usr/bin/env python3
"""
TODOIT Web Interface Launcher
Simple script to start the web application with proper configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Ensure we're in the correct directory
    web_dir = Path(__file__).parent
    os.chdir(web_dir)
    
    # Set default database path if not set
    if not os.environ.get('TODOIT_DB_PATH'):
        os.environ['TODOIT_DB_PATH'] = '/tmp/test_todoit.db'
    
    print("🚀 Starting TODOIT Web Interface...")
    print(f"📁 Working directory: {web_dir}")
    print(f"🗄️  Database path: {os.environ['TODOIT_DB_PATH']}")
    print(f"🌐 URL: http://localhost:8000")
    print("-" * 50)
    
    # Start uvicorn server
    try:
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload"
        ]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Shutting down TODOIT Web Interface...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()