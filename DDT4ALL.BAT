@echo off
echo Activate venv
call venv\Scripts\activate.bat
rem pip install --upgrade pip
pip install -r requirements.txt
python.exe ddt4all.py
echo Deactivate venv
call venv\Scripts\deactivate.bat
pause