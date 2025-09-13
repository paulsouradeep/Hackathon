#!/usr/bin/env python3
"""
Telus AI Talent Intelligence Platform - Quick Run Script
This script starts the application with proper configuration
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def check_setup():
    """Check if the project is properly set up"""
    required_files = [
        "app.py",
        "requirements.txt",
        "models/ai_models.py",
        "data/jobs/jobs.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n💡 Please run setup first: python3 setup.py")
        return False
    
    return True

def check_dependencies():
    """Check if dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import sentence_transformers
        import faiss
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Please run: python3 setup.py")
        return False

def start_application():
    """Start the FastAPI application"""
    print("🚀 Starting Telus AI Talent Intelligence Platform...")
    print("📍 Server will be available at: http://localhost:8081")
    print("⏳ Loading AI models (this may take a moment)...")
    
    try:
        # Import and run the application
        import uvicorn
        from app import app
        
        print("✅ Application starting...")
        print("🌐 Opening browser in 3 seconds...")
        
        # Start server in a separate process and open browser
        def open_browser():
            time.sleep(3)
            webbrowser.open("http://localhost:8081")
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start the server
        uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("💡 Try running setup again: python3 setup.py")

def main():
    """Main function"""
    print("🎯 Telus AI Talent Intelligence Platform")
    print("=" * 45)
    
    # Check if setup is complete
    if not check_setup():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Start application
    start_application()

if __name__ == "__main__":
    main()
