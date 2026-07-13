#!/usr/bin/env python3
"""Start the Codebase Genius API server with proper environment setup."""
import os
import sys

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set default environment variables if not already set
if not os.getenv('USE_LLM'):
    os.environ['USE_LLM'] = 'true'

# Check if API key is set
if not os.getenv('GEMINI_API_KEY'):
    print("⚠️  Warning: GEMINI_API_KEY not set. LLM features will be disabled.")
    print("   Set it in .env file or as environment variable")

import uvicorn
from codebase_genius.api_server import app

if __name__ == "__main__":
    # Support PORT environment variable for deployment platforms
    port = int(os.getenv('PORT', sys.argv[1] if len(sys.argv) > 1 else 8000))
    
    print("=" * 70)
    print("🧠 CODEBASE GENIUS API SERVER")
    print("=" * 70)
    print(f"\n📡 Server starting on http://0.0.0.0:{port}")
    print(f"🎨 GUI available at http://0.0.0.0:{port}/gui")
    print(f"📊 API docs at http://0.0.0.0:{port}/docs")
    print(f"❤️  Health check at http://0.0.0.0:{port}/health")
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
