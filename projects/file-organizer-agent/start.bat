@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo Starting File Organizer Agent Web UI...
echo.
python run.py --web
pause
