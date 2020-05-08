@echo off

SET PROGRAM-NAME=DDT4All
SET FILE-NAME=ddt4all

SET CHARACTERS=400
SET XGETTEXT-OPTIONS=--from-code=UTF-8 --no-location --width=%CHARACTERS% --no-wrap

CLS
ECHO *********************************************
ECHO * %PROGRAM-NAME%
ECHO * Create master language template
ECHO *********************************************

ECHO.
ECHO.
ECHO     #### Press any key to continue ####
ECHO     ####   Press CTRL+C to break   ####
PAUSE >NUL

CLS
ECHO *********************************************
ECHO * %PROGRAM-NAME%
ECHO * Create master language template
ECHO *********************************************

ECHO.
ECHO Creating master language template '../locale/%FILE-NAME%.pot'...

xgettext %XGETTEXT-OPTIONS% -f python_files_Windows.txt -o ../locale/%FILE-NAME%.pot  > NUL

ECHO Creating master language template '../locale/%FILE-NAME%.pot' completed!

ECHO.
ECHO.
ECHO    #### Press any key to exit ####
PAUSE > NUL

SET PROGRAM-NAME=
SET FILE-NAME=
SET CHARACTERS=
SET XGETTEXT-OPTIONS=
