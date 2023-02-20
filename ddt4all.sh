#!/bin/bash
#chmod +x ./ddt4all.py
printf "Install new venv ...\n"
#Install venv if not present
python3 -m venv ./venv
printf "Activate venv ...\n"
chmod +x ./venv/bin/activate
source ./venv/bin/activate
# Linux ubuntu fixes uncomment next lines
# Fix qt platform plugin linux ubuntu "xcb" if error's
#sudo apt-get install --reinstall libxcb-xinerama0
./venv/bin/python3 -m pip install --upgrade pip
printf "Install requirements ...\n"
./venv/bin/pip install -r ./requirements.txt
printf "Runs app ...\n"
./venv/bin/python3 ./main.py