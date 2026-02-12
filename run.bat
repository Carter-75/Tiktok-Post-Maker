@echo off
cd /d "%~dp0"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

echo Checking dependencies...
pip install -r requirements.txt

python tiktok_generator.py
pause
