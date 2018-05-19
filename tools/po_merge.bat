@ECHO OFF
CLS
SETLOCAL EnableExtensions 

ECHO *********************************************************************
for %%x in (de es fr hu it nl pl pt ru sr) do (

ECHO **** Country = %%x - Merging 'ddt4all.po' with 'ddt4all.pot' template....
msgmerge  -U -v -N --backup=none ..\locale\%%x\lc_messages\ddt4all.po ..\locale\ddt4all.pot
REM msgattrib --no-obsolete ..\locale\it\lc_messages\ddt4all.po > ..\locale\%%x\lc_messages\ddt4all_new.po
REM copy ..\locale\%%x\lc_messages\ddt4all_new.po ..\locale\it\lc_messages\ddt4all.po
REM del ..\locale\%%x\lc_messages\ddt4all_new.po
ECHO *********************************************************************
)

ECHO.
ECHO.
ECHO      **** Press any key to exit ****
pause >NUl
