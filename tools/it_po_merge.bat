@ECHO OFF
CLS

SET FILE=ddt4all
ECHO.
ECHO **** Merging '%FILE%.po' with '%FILE%.pot' template....
msgmerge  -U -v --backup=none ..\locale\it\lc_messages\%FILE%.po ..\locale\%FILE%.pot

SET FILE=ddt4all_main
ECHO.
ECHO.
ECHO **** Merging '%FILE%.po' with '%FILE%.pot' template....
msgmerge  -U -v --backup=none ..\locale\it\lc_messages\%FILE%.po ..\locale\%FILE%.pot

SET FILE=dataeditor
ECHO.
ECHO.
ECHO **** Merging '%FILE%.po' with '%FILE%.pot' template....
msgmerge  -U -v --backup=none ..\locale\it\lc_messages\%FILE%.po ..\locale\%FILE%.pot

SET FILE=elm
ECHO.
ECHO.
ECHO **** Merging '%FILE%.po' with '%FILE%.pot' template....
msgmerge  -U -v --backup=none ..\locale\it\lc_messages\%FILE%.po ..\locale\%FILE%.pot


ECHO.
ECHO.
ECHO      **** Press any key to exit ****
pause >NUl
