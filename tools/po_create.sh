#/bin/sh

xgettext elm.py -o locale/elm.pot --from-code=UTF-8
xgettext parameters.py -o locale/ddt4all.pot --from-code=UTF-8
xgettext main.py -o locale/ddt4all_main.pot --from-code=UTF-8
xgettext dataeditor.py -o locale/dataeditor.pot --from-code=UTF-8
