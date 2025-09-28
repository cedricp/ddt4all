#/bin/sh

xgettext elm.py -o locale/elm.pot --from-code=UTF-8
xgettext parameters.py -o locale/ddt4all.pot --from-code=UTF-8
xgettext main.py -o locale/ddt4all_main.pot --from-code=UTF-8
xgettext dataeditor.py -o locale/dataeditor.pot --from-code=UTF-8
xgettext displaymod.py -o locale/displaymod.pot --from-code=UTF-8
xgettext ecu.py -o locale/ecu.pot --from-code=UTF-8
xgettext package.py -o locale/package.pot --from-code=UTF-8
xgettext sniffer.py -o locale/sniffer.pot --from-code=UTF-8
xgettext usbdevice.py -o locale/usbdevice.pot --from-code=UTF-8
xgettext uiutils.py -o locale/uiutils.pot --from-code=UTF-8
