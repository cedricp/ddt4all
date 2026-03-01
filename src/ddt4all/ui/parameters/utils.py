import glob
from io import BytesIO
import json
import os
from pathlib import Path
import xml.dom.minidom
import zipfile

from ddt4all.core.ecu.ecu_file import EcuFile
import ddt4all.options as options
from ddt4all.ui.utils import (
    colorConvert,
    getChildNodesByName,
    getFontColor,
    getFontXML,
    getRectangleXML,
)

_ = options.translator('ddt4all')

BASE_DIR = Path(__file__).resolve().parent
PATH_PNG_ODB = str(BASE_DIR / ".." / ".." / "resources" / "icons" / "odb.png")


def zipConvertXML(dbfilename="ecu.zip"):
    zipoutput = BytesIO()
    options.ecus_dir = "./ecus"

    ecus_glob = glob.glob("ecus/*.xml")
    imgs = []
    if os.path.exists("./graphics"):
        for dirpath, dirs, files in os.walk("graphics/"):
            for file in files:
                if ".gif" in file.lower():
                    imgs.append(os.path.join(dirpath, file))

    if len(ecus_glob) == 0:
        print(_("Cannot zip database, no 'ecus' directory"))
        return

    ecus = []
    for e in ecus_glob:
        if 'eculist.xml' in e.lower():
            continue
        ecus.append(e)

    i = 1
    print(_("Starting conversion"))

    targetsdict = {}
    with zipfile.ZipFile(zipoutput, mode='w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for img in imgs:
            zf.write(img)
        for target in ecus:
            filename = target.replace(".xml", ".json")
            if filename.startswith("ecus/"):
                filename = filename.replace("ecus/", "")
            else:
                filename = filename.replace("ecus\\", "")
            print(_("Starting processing ") + target + " " + str(i) + "/" + str(len(ecus)) + _(" to ") + filename)

            i += 1
            layoutjs = dumpXML(target)
            if layoutjs is None:
                print(_("Skipping current file (cannot parse it)"))
                continue
            ecufile = EcuFile(target, True)
            js = ecufile.dumpJson()

            if js:
                zf.writestr(filename, str(js))

            if layoutjs:
                zf.writestr(filename + ".layout", str(layoutjs))

            ecu_ident = ecufile.dump_idents()

            targetsdict[filename] = ecu_ident

        print(_("Writing database"))
        zf.writestr("db.json", str(json.dumps(targetsdict, indent=1)))

    print(_("Writing archive"))
    with open(dbfilename, "wb") as f:
        f.write(zipoutput.getvalue())

def dumpXML(xmlname):
    try:
        xdom = xml.dom.minidom.parse(xmlname)
        xdoc = xdom.documentElement
    except Exception:
        return None
    return dumpDOC(xdoc)

def dumpDOC(xdoc):
    target = getChildNodesByName(xdoc, u"Target")
    if not target:
        return None

    target = target[0]
    js_screens = {}

    xml_categories = getChildNodesByName(target, u"Categories")

    xmlscreens = {}
    js_categories = {}

    for cats in xml_categories:
        xml_cats = getChildNodesByName(cats, u"Category")
        for category in xml_cats:
            category_name = category.getAttribute(u"Name")
            js_categories[category_name] = []
            screens_name = getChildNodesByName(category, u"Screen")
            for screen in screens_name:
                screen_name = screen.getAttribute(u"Name")
                xmlscreens[screen_name] = screen
                js_categories[category_name].append(screen_name)

    for scrname, screen in xmlscreens.items():
        screen_name = scrname
        js_screens[screen_name] = {}
        js_screens[screen_name]['width'] = int(screen.getAttribute("Width"))
        js_screens[screen_name]['height'] = int(screen.getAttribute("Height"))
        js_screens[screen_name]['color'] = colorConvert(screen.getAttribute("Color"))
        js_screens[screen_name]['labels'] = {}

        presend = []
        for elem in getChildNodesByName(screen, u"Send"):
            delay = elem.getAttribute('Delay')
            req_name = elem.getAttribute('RequestName')
            presend.append({"Delay": delay, "RequestName": req_name})
        js_screens[screen_name]['presend'] = presend

        labels = getChildNodesByName(screen, "Label")
        js_screens[screen_name]['labels'] = []
        for label in labels:
            label_dict = {}
            label_dict['text'] = label.getAttribute("Text")
            label_dict['color'] = colorConvert(label.getAttribute("Color"))
            label_dict['alignment'] = label.getAttribute("Alignment")
            label_dict['fontcolor'] = getFontColor(label)
            label_dict['bbox'] = getRectangleXML(getChildNodesByName(label, "Rectangle")[0])
            label_dict['font'] = getFontXML(label)
            js_screens[screen_name]['labels'].append(label_dict)

        displays = getChildNodesByName(screen, "Display")
        js_screens[screen_name]['displays'] = []
        for display in displays:
            display_dict = {}
            display_dict['text'] = display.getAttribute("DataName")
            display_dict['request'] = display.getAttribute("RequestName")
            display_dict['color'] = colorConvert(display.getAttribute("Color"))
            display_dict['width'] = int(display.getAttribute("Width"))
            display_dict['rect'] = getRectangleXML(getChildNodesByName(display, "Rectangle")[0])
            display_dict['font'] = getFontXML(display)
            display_dict['fontcolor'] = getFontColor(display)
            js_screens[screen_name]['displays'].append(display_dict)

        buttons = getChildNodesByName(screen, "Button")
        js_screens[screen_name]['buttons'] = []
        count = 0
        for button in buttons:
            button_dict = {}
            txt = button.getAttribute("Text")
            button_dict['text'] = txt
            button_dict['uniquename'] = txt + "_%i" % count
            button_dict['rect'] = getRectangleXML(getChildNodesByName(button, "Rectangle")[0])
            button_dict['font'] = getFontXML(button)

            xmlmessages = getChildNodesByName(button, "Message")
            messages = []
            # Get messages
            for message in xmlmessages:
                messages.append(message.getAttribute("Text"))

            button_dict['messages'] = messages

            send = getChildNodesByName(button, "Send")
            if send:
                sendlist = []
                for snd in send:
                    smap = {}
                    delay = snd.getAttribute("Delay")
                    reqname = snd.getAttribute("RequestName")
                    smap['Delay'] = delay
                    smap['RequestName'] = reqname
                    sendlist.append(smap)
                button_dict['send'] = sendlist

            js_screens[screen_name]['buttons'].append(button_dict)
            count += 1

        inputs = getChildNodesByName(screen, "Input")
        js_screens[screen_name]['inputs'] = []

        for input in inputs:
            input_dict = {}
            input_dict['text'] = input.getAttribute("DataName")
            input_dict['request'] = input.getAttribute("RequestName")
            color = input.getAttribute("Color")
            if not color:
                color = 0xAAAAAA
            input_dict['color'] = colorConvert(color)
            input_dict['fontcolor'] = getFontColor(input)
            input_dict['width'] = int(input.getAttribute("Width"))
            input_dict['rect'] = getRectangleXML(getChildNodesByName(input, "Rectangle")[0])
            input_dict['font'] = getFontXML(input)
            js_screens[screen_name]['inputs'].append(input_dict)

    return json.dumps({'screens': js_screens, 'categories': js_categories}, indent=1)
