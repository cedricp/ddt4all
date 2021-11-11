@echo off
call venv\Scripts\activate.bat
pip install -r requirements.txt
python.exe ddt4all.py
pause