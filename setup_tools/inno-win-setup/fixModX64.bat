@echo off
echo Installing or fixing dependencies...
echo.
.\Python313-x64\python.exe -m pip install -e ".[dev,can,network,bluetooth]" --no-warn-script-location
echo.
echo Done.
if "%1"=="-p" pause