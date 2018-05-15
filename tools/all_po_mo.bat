@ECHO OFF
CLS

ECHO *****************************************************************
for %%x in (de es fr hu it nl pl pt ru sr) do (

ECHO **** Country = %%x - Compiling 'ddt4all.po' in 'ddt4all.mo'....
msgfmt ..\locale\it\lc_messages\ddt4all.po -o ..\locale\it\lc_messages\ddt4all.mo
ECHO **** Country = %%x - Compiling 'ddt4all_main.po' in 'ddt4all_main.mo'....
msgfmt ..\locale\it\lc_messages\ddt4all_main.po -o ..\locale\it\lc_messages\ddt4all_main.mo
ECHO **** Country = %%x - Compiling 'dataeditor.po' in 'dataeditor.mo'....
msgfmt ..\locale\it\lc_messages\dataeditor.po -o ..\locale\it\lc_messages\dataeditor.mo
ECHO **** Country = %%x - Compiling 'elm.po' in 'elm.mo'....
msgfmt ..\locale\it\lc_messages\elm.po -o ..\locale\it\lc_messages\elm.mo

ECHO *****************************************************************
)

ECHO.
ECHO.
ECHO      **** Press any key to exit ****

pause >NUl
