@ECHO OFF
CLS

ECHO *****************************************************************
for %%x in (de es fr hu it nl pl pt ru sr) do (
ECHO **** Country = %%x - Compiling 'ddt4all.po' in 'ddt4all.mo'....
msgfmt ..\locale\%%x\lc_messages\ddt4all.po -o ..\locale\%%x\lc_messages\ddt4all.mo
ECHO *****************************************************************
)

ECHO.
ECHO.
ECHO      **** Press any key to exit ****

pause >NUl
