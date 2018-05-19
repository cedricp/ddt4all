@echo off
CLS

xgettext -f python_files.txt -o ../locale/ddt4all.pot --from-code=UTF-8

ECHO.
ECHO    #### Press any key to exit ####
pause >NUl
