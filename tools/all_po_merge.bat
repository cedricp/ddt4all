@ECHO OFF
CLS
SETLOCAL EnableExtensions 

ECHO *********************************************************************
for %%x in (de es fr hu it nl pl pt ru sr) do (


SET FILE=ddt4all
ECHO **** Country = %%x - Merging 'ddt4all.po' with 'ddt4all.pot' template....
msgmerge  -U -v --backup=none ..\locale\%%x\lc_messages\ddt4all.po ..\locale\ddt4all.pot
msgattrib --no-obsolete ..\locale\it\lc_messages\ddt4all.po > ..\locale\%%x\lc_messages\ddt4all.po
ECHO **** Country = %%x - Merging 'ddt4all_main.po' with 'ddt4all_main.pot' template....
msgmerge  -U -v --backup=none ..\locale\%%x\lc_messages\ddt4all_main.po ..\locale\ddt4all_main.pot
msgattrib --no-obsolete ..\locale\%%x\lc_messages\ddt4all_main.po > ..\locale\%%x\lc_messages\ddt4all_main.po
ECHO **** Country = %%x - Merging 'dataeditor.po' with 'dataeditor.pot' template....
msgmerge  -U -v --backup=none ..\locale\%%x\lc_messages\dataeditor.po ..\locale\dataeditor.pot
msgattrib --no-obsolete ..\locale\%%x\lc_messages\dataeditor.po > ..\locale\%%x\lc_messages\dataeditor.po
ECHO **** Country = %%x - Merging 'elm.po' with 'elm.pot' template....
msgmerge  -U -v --backup=none ..\locale\%%x\lc_messages\elm.po ..\locale\elm.pot
msgattrib --no-obsolete ..\locale\%%x\lc_messages\elm.po > ..\locale\%%x\lc_messages\elm.po
ECHO *********************************************************************
)

ECHO.
ECHO.
ECHO      **** Press any key to exit ****
pause >NUl
