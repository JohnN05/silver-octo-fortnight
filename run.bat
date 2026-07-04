@echo off
:: Run script for Windows Task Scheduler using Python Virtual Environment
cd /d "%~dp0"
call .venv\Scripts\activate
python main.py
echo Ticket Tracker Execution Finished.
pause
