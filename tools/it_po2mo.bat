@ECHO OFF
CLS

SET FILE=ddt4all
ECHO.
ECHO **** Compiling '%FILE%.po' in '%FILE%.mo'....
msgfmt -v ..\locale\it\lc_messages\%FILE%.po -o ..\locale\it\lc_messages\%FILE%.mo

SET FILE=ddt4all_main
ECHO.
ECHO.
ECHO **** Compiling '%FILE%.po' in '%FILE%.mo'....
msgfmt -v ..\locale\it\lc_messages\%FILE%.po -o ..\locale\it\lc_messages\%FILE%.mo

SET FILE=dataeditor
ECHO.
ECHO.
ECHO **** Compiling '%FILE%.po' in '%FILE%.mo'....
msgfmt -v ..\locale\it\lc_messages\%FILE%.po -o ..\locale\it\lc_messages\%FILE%.mo

SET FILE=elm
ECHO.
ECHO.
ECHO **** Compiling '%FILE%.po' in '%FILE%.mo'....
msgfmt -v ..\locale\it\lc_messages\%FILE%.po -o ..\locale\it\lc_messages\%FILE%.mo


ECHO.
ECHO.
ECHO      **** Press any key to exit ****

pause >NUl
