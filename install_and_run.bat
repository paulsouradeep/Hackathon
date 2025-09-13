@echo off
REM Telus AI Talent Intelligence Platform - One-Click Setup & Run Script
REM This script works on Windows

echo 🚀 Telus AI Talent Intelligence Platform - One-Click Setup
echo ==========================================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH.
    echo 💡 Please install Python 3.8+ from: https://python.org/downloads
    echo 💡 Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo ✅ Found Python %python_version%

echo.
echo 🔧 Running setup...
python setup.py

REM Check if setup was successful
if %errorlevel% equ 0 (
    echo.
    echo 🎉 Setup completed successfully!
    echo.
    echo 🚀 Starting the application...
    python run_project.py
) else (
    echo ❌ Setup failed. Please check the error messages above.
    pause
    exit /b 1
)
