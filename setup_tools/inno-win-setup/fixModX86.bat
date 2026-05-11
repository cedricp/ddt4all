@echo off
echo Installing or fixing dependencies...
echo.
.\Python386-32\python.exe -m pip install -e ".[dev,can,network,bluetooth]" --no-warn-script-location
echo.
echo Done.
if "%1"=="-p" pause