#!/bin/bash
chmod +x ./venv/bin/activate
#chmod +x ./ddt4all.py
printf "Activate venv ...\n"
./venv/bin/activate
python -m pip install --upgrade pip
printf "Install requirements ...\n"
pip install -r ./requirements.txt
printf "Runs app ...\n"
python ./ddt4all.py
#printf "Deactivate venv ..."
#./venv/bin/deactivate