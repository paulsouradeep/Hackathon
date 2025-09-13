#!/usr/bin/env python3
"""
Quick Demo Runner for Telus Talent Intelligence Platform
Sets up and runs the complete demo environment
"""

import subprocess
import sys
import os
import time

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    return True

def load_demo_data():
    """Load sample candidates into the database"""
    print("🔄 Loading demo data...")
    try:
        subprocess.check_call([sys.executable, "demo_data_loader.py"])
        print("✅ Demo data loaded successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error loading demo data: {e}")
        return False
    return True

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Telus Talent Intelligence Platform...")
    print("📊 Dashboard will be available at: http://localhost:8080")
    print("📤 Upload page will be available at: http://localhost:8080/upload")
    print("\n🔥 Press Ctrl+C to stop the server\n")
    
    try:
        subprocess.check_call([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Thank you for trying the demo!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main demo runner"""
    print("🧠 Telus Talent Intelligence Platform - Demo Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Load demo data
    if not load_demo_data():
        sys.exit(1)
    
    print("\n🎉 Demo setup complete!")
    print("\n📋 What you can demo:")
    print("   • AI-powered resume matching")
    print("   • Multi-role candidate redirection")
    print("   • Confidence-based routing (AUTO/REVIEW/HUMAN)")
    print("   • Human-in-the-loop feedback system")
    print("   • Skill gap analysis and training recommendations")
    print("   • Real-time analytics dashboard")
    
    print("\n🎯 Demo Flow:")
    print("   1. Visit http://localhost:8080 for the recruiter dashboard")
    print("   2. View pre-loaded sample candidates with AI matches")
    print("   3. Click on any candidate to see detailed analysis")
    print("   4. Try uploading a new resume at /upload")
    print("   5. Provide feedback to see the HITL system in action")
    
    input("\n⏳ Press Enter to start the server...")
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()
