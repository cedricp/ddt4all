@ECHO OFF
SETLOCAL EnableExtensions 

SET PROGRAM-NAME=DDT4All
SET FILE-NAME=ddt4all

SET LANGUAGES=de es fr hu it nl pl pt ro ru sr
SET MSGFMT-OPTIONS=--statistics

CLS
ECHO ********************************************************
ECHO * %PROGRAM-NAME%
ECHO * Show statistics about language files
ECHO ********************************************************
ECHO.
ECHO.
ECHO            #### Press any key to continue ####
ECHO            ####   Press CTRL+C to break   ####
PAUSE >NUL

CLS
ECHO ********************************************************
ECHO * %PROGRAM-NAME%
ECHO * Show statistics about language files
ECHO ********************************************************
ECHO.
for %%x in (%LANGUAGES%) do (
   ECHO **** Country = %%x - Statistics about '%FILE-NAME%.po'....
   msgfmt %MSGFMT-OPTIONS% ..\locale\%%x\lc_messages\%FILE-NAME%.po
   ECHO. 
)

if exist Messages.mo del Messages.mo > NUL

ECHO.
ECHO.
ECHO      #### Press any key to exit #####
PAUSE > NUL

SET PROGRAM-NAME=
SET FILE-NAME=
SET LANGUAGES=
SET MSGFMT-OPTIONS=

