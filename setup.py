#!/usr/bin/env python3
"""
Telus AI Talent Intelligence Platform Setup Script
This script sets up the entire project with all dependencies
"""

import subprocess
import sys
import os
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}:")
        print(f"Command: {command}")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install all required dependencies"""
    print("\n📦 Installing dependencies...")
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Try minimal requirements first, then full requirements
    if not run_command(f"{sys.executable} -m pip install -r requirements_minimal.txt", "Installing core Python packages"):
        print("⚠️  Core installation failed, trying full requirements...")
        if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing all Python packages"):
            print("❌ Both installation attempts failed")
            print("💡 Try manual installation: pip install fastapi uvicorn sentence-transformers faiss-cpu")
            return False
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        "static",
        "data/jobs",
        "data/resumes",
        "models",
        "templates",
        "config"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_database():
    """Initialize the database"""
    print("\n🗄️ Setting up database...")
    try:
        # Import and initialize the app to create database
        from app import init_db
        init_db()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Telus AI Talent Intelligence Platform Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    print("\n📁 Creating project directories...")
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("\n❌ Setup failed during database initialization")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run the application: python3 app.py")
    print("2. Or use the run script: python3 run_project.py")
    print("3. Open your browser to: http://localhost:8081")
    print("\n💡 For more information, see README_SETUP.md")

if __name__ == "__main__":
    main()
