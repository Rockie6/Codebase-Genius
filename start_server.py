#!/usr/bin/env python3
"""Start the Codebase Genius API server (loads your .env for you)."""
import os
import sys

from codebase_genius import load_env
load_env()

# Set default environment variables if not already set
if not os.getenv('USE_LLM'):
    os.environ['USE_LLM'] = 'true'

# Check if API key is set
if not os.getenv('GEMINI_API_KEY'):
    print("⚠️  No GEMINI_API_KEY found — that's fine, the fancy LLM extras will just be skipped.")
    print("   To enable them, drop a key in your .env file (see .env.example).")

import uvicorn
from codebase_genius.api_server import app

if __name__ == "__main__":
    # Support PORT environment variable for deployment platforms
    port = int(os.getenv('PORT', sys.argv[1] if len(sys.argv) > 1 else 8000))
    
    print("=" * 70)
    print("🧠 CODEBASE GENIUS API SERVER")
    print("=" * 70)
    print(f"\n📡 Server starting on http://0.0.0.0:{port}")
    print(f"🎨 Web UI:    http://0.0.0.0:{port}/gui")
    print(f"📊 API docs:  http://0.0.0.0:{port}/docs")
    print(f"❤️  Health:    http://0.0.0.0:{port}/health")
    print("\nPress CTRL+C any time to stop the server\n")
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
