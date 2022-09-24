#!/bin/bash
chmod +x ./venv/bin/activate
#chmod +x ./ddt4all.py
## Linux ubuntu fixes uncomment next lines
#printf "Install new venv ...\n"
#Install venv if not present
#python3 -m venv ./venv
#fix qt platform plugin ubuntu "xcb"
#sudo apt-get install --reinstall libxcb-xinerama0
##
printf "Activate venv ...\n"
./venv/bin/activate
./venv/bin/python -m pip install --upgrade pip
printf "Install requirements ...\n"
./venv/bin/pip install -r ./requirements.txt
printf "Runs app ...\n"
./venv/bin/python ./main.py
#printf "Deactivate venv ..."
#./venv/bin/deactivate