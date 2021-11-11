@echo off
call venv\Scripts\activate.bat
rem pip install --upgrade pip
pip install -r requirements.txt
python.exe ddt4all.py
rem pause