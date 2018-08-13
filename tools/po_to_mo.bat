@ECHO OFF
CLS
ECHO ******************************************
ECHO * DDT4ALL - Convert PO files in MO files *
ECHO ******************************************
ECHO.
ECHO.
ECHO      #### Press any key to continue ####
ECHO      ####   Press CTRL+C to break   ####
PAUSE >NUL

CLS
ECHO ******************************************
ECHO * DDT4ALL - Convert PO files in MO files *
ECHO ******************************************
ECHO.

for %%x in (de es fr hu it nl pl pt ru sr) do (

ECHO **** Country = %%x - Compiling 'ddt4all.po' in 'ddt4all.mo'....
msgfmt ..\locale\%%x\lc_messages\ddt4all.po -o ..\locale\%%x\lc_messages\ddt4all.mo > NUL
ECHO.
)

ECHO.
ECHO.
ECHO      #### Press any key to exit ####

PAUSE > NUL
