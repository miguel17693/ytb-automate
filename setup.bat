@echo off
REM Quick setup script for Windows

echo ===================================
echo 🎤 Karaoke Automation System - Quick Setup
echo ===================================
echo.

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.9+
    pause
    exit /b 1
)
echo ✅ Python found

REM Check FFmpeg
echo.
echo Checking FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ FFmpeg not found. Please install FFmpeg:
    echo    Download from: https://www.gyan.dev/ffmpeg/builds/
    echo    Add to PATH
    pause
    exit /b 1
)
echo ✅ FFmpeg found

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat
echo ✅ Virtual environment created

REM Install dependencies
echo.
echo Installing dependencies (this may take a while)...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo ✅ Dependencies installed

REM Create .env file
if not exist .env (
    echo.
    echo Creating .env file...
    copy .env.example .env
    echo ⚠️  Please edit .env and add your YouTube API key
)

echo.
echo ===================================
echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Edit .env and add your YouTube API key
echo 2. (Optional^) Download client_secrets.json for YouTube upload
echo 3. Run: python main.py
echo.
echo Happy karaoke-ing! 🎤
echo.
pause
