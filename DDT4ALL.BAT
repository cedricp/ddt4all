@echo off
echo Activate venv
call venv\Scripts\activate.bat
pip install -U pip virtualenv
virtualenv --system-site-packages -p python ./venv
rem pip install --upgrade pip
pip install -r requirements.txt
python.exe ddt4all.py
echo Deactivate venv
call venv\Scripts\deactivate.bat
pause