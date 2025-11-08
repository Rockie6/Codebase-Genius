#!/usr/bin/env python3
"""Start the Codebase Genius API server with proper environment setup."""
import os
import sys

# Set environment variables
os.environ['USE_LLM'] = 'true'
os.environ['GEMINI_API_KEY'] = 'AIzaSyDYGtyz_5AfplZi0Og185BOX_8JO767i2w'

import uvicorn
from codebase_genius.api_server import app

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    print("=" * 70)
    print("🧠 CODEBASE GENIUS API SERVER")
    print("=" * 70)
    print(f"\n📡 Server starting on http://localhost:{port}")
    print(f"🎨 GUI available at http://localhost:{port}/gui")
    print(f"📊 API docs at http://localhost:{port}/docs")
    print(f"❤️  Health check at http://localhost:{port}/health")
    print("\nPress CTRL+C to stop the server\n")
    print("=" * 70)
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
