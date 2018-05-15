xgettext ..\elm.py        -o ../locale/elm.pot          --from-code=UTF-8
xgettext ..\parameters.py -o ../locale/ddt4all.pot      --from-code=UTF-8
xgettext ..\ddt4all.py    -o ../locale/ddt4all_main.pot --from-code=UTF-8
xgettext ..\dataeditor.py -o ../locale/dataeditor.pot   --from-code=UTF-8

xgettext ..\ddtplugins\ab90_reset.py -o plugins.pot  --from-code=UTF-8

pause >NUl
