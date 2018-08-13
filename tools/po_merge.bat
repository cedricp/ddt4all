@ECHO OFF
SETLOCAL EnableExtensions 

CLS
ECHO ********************************************************
ECHO * DDTALL - Update language files using master template *
ECHO ********************************************************
ECHO.
ECHO.
ECHO            #### Press any key to continue ####
ECHO            ####   Press CTRL+C to break   ####
PAUSE >NUL

CLS
ECHO ********************************************************
ECHO * DDTALL - Update language files using master template *
ECHO ********************************************************
for %%x in (de es fr hu it nl pl pt ru sr) do (

ECHO **** Country = %%x - Merging 'ddt4all.po' with 'ddt4all.pot' template....
msgmerge  -U -q -N --backup=none ..\locale\%%x\lc_messages\ddt4all.po ..\locale\ddt4all.pot >NUL
ECHO **** Country = %%x - Cleaning obsolete entries from 'ddt4all.po'....
msgattrib --no-obsolete ..\locale\%%x\lc_messages\ddt4all.po > ..\locale\%%x\lc_messages\ddt4all_new.po
copy ..\locale\%%x\lc_messages\ddt4all_new.po ..\locale\%%x\lc_messages\ddt4all.po >NUL
del ..\locale\%%x\lc_messages\ddt4all_new.po >NUL
ECHO **** Country = %%x - Statistics about 'ddt4all.po'....
msgfmt --statistics ..\locale\%%x\lc_messages\ddt4all.po
REM msgattrib --no-obsolete ..\locale\it\lc_messages\ddt4all.po > ..\locale\%%x\lc_messages\ddt4all_new.po
REM copy ..\locale\%%x\lc_messages\ddt4all_new.po ..\locale\it\lc_messages\ddt4all.po
REM del ..\locale\%%x\lc_messages\ddt4all_new.po
ECHO *******************************************************

)

if exist Messages.mo del Messages.mo > NUL

ECHO.
ECHO.
ECHO      #### Press any key to exit #####
PAUSE > NUL
