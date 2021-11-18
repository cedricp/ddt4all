#!/bin/bash
chmod +x ./venv/bin/activate
printf "Activate venv ..."
./venv/bin/activate
python -m pip install --upgrade pip
printf "Install requirements ..."
pip install -r requirements.txt
printf "Runs app ..."
python ddt4all.py
#printf "Deactivate venv ..."
#./venv/bin/deactivate