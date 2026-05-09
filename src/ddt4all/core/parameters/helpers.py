import glob
from io import BytesIO
import json
import os
import xml.dom.minidom
import zipfile

from ddt4all.core.ecu.ecu_database import (
    EcuDatabase,
    addressing
)
from ddt4all.core.ecu.ecu_file import EcuFile
import ddt4all.core.elm.elm as elm
from ddt4all.file_manager import get_dir
import ddt4all.options as options
from ddt4all.ui.utils import (
    colorConvert,
    getChildNodesByName,
    getFontColor,
    getFontXML,
    getRectangleXML,
)

_ = options.translator('ddt4all')

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

    folder_29 = []
    if os.path.exists("./$29"):
        for dirpath, dirs, files in os.walk("$29/"):
            for file in files:
                folder_29.append(os.path.join(dirpath, file))

    folder_utt = []
    if os.path.exists("./utt_certificates"):
        for dirpath, dirs, files in os.walk("utt_certificates/"):
            for file in files:
                folder_utt.append(os.path.join(dirpath, file))

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
        for file_29 in folder_29:
            zf.write(file_29)
        for file_utt in folder_utt:
            zf.write(file_utt)
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

def dumpAddressing(file):
    xdom = xml.dom.minidom.parse(file)
    xdoc = xdom.documentElement
    dictionary = addressing
    xml_funcs = getChildNodesByName(xdoc, u"Function")
    for func in xml_funcs:
        shortname = func.getAttribute(u"Name")
        address = func.getAttribute(u"Address")
        for name in getChildNodesByName(func, u"Name"):
            try:
                if str(name.firstChild.nodeValue).startswith("\n"):
                    longname = shortname
                else:
                    longname = name.firstChild.nodeValue
            except Exception:
                longname = shortname

            strHex = "%0.2X" % int(address)
            dictionary[strHex] = (shortname, longname)
            break
    return dictionary


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


def dumpSNAT(file):
    xdom = xml.dom.minidom.parse(file)
    xdoc = xdom.documentElement
    dictionary = elm.snat
    xml_funcs = getChildNodesByName(xdoc, u"Function")
    for func in xml_funcs:
        address = func.getAttribute(u"Address")
        protolist = getChildNodesByName(func, u"ProtocolList")
        for rid in protolist:
            proto = getChildNodesByName(rid, u"Protocol")
            for prtc in proto:
                grid = getChildNodesByName(prtc, u"Address")
                for ok in grid:
                    ext = ok.getAttribute(u"Extended")
                    if ext == "0":
                        rid_add = ok.getAttribute(u"Rid")
                        strHex = "%0.2X" % int(address)
                        dictionary[strHex] = rid_add
                        break
    return dictionary


def dumpSNAT_ext(file):
    xdom = xml.dom.minidom.parse(file)
    xdoc = xdom.documentElement
    dictionary = elm.snat_ext
    xml_funcs = getChildNodesByName(xdoc, u"Function")
    for func in xml_funcs:
        address = func.getAttribute(u"Address")
        protolist = getChildNodesByName(func, u"ProtocolList")
        for rid in protolist:
            proto = getChildNodesByName(rid, u"Protocol")
            for prtc in proto:
                grid = getChildNodesByName(prtc, u"Address")
                for ok in grid:
                    ext = ok.getAttribute(u"Extended")
                    if ext == "1":
                        rid_add = ok.getAttribute(u"Rid")
                        strHex = "%0.2X" % int(address)
                        dictionary[strHex] = rid_add
                        break
    return dictionary


def dumpDNAT(file):
    xdom = xml.dom.minidom.parse(file)
    xdoc = xdom.documentElement
    dictionary = elm.dnat
    xml_funcs = getChildNodesByName(xdoc, u"Function")
    for func in xml_funcs:
        address = func.getAttribute(u"Address")
        protolist = getChildNodesByName(func, u"ProtocolList")
        for xid in protolist:
            proto = getChildNodesByName(xid, u"Protocol")
            for prtc in proto:
                gxid = getChildNodesByName(prtc, u"Address")
                for ok in gxid:
                    ext = ok.getAttribute(u"Extended")
                    if ext == "0":
                        xid_add = ok.getAttribute(u"Xid")
                        strHex = "%0.2X" % int(address)
                        dictionary[strHex] = xid_add
                        break
    return dictionary


def dumpDNAT_ext(file):
    xdom = xml.dom.minidom.parse(file)
    xdoc = xdom.documentElement
    dictionary = elm.dnat_ext
    xml_funcs = getChildNodesByName(xdoc, u"Function")
    for func in xml_funcs:
        address = func.getAttribute(u"Address")
        protolist = getChildNodesByName(func, u"ProtocolList")
        for xid in protolist:
            proto = getChildNodesByName(xid, u"Protocol")
            for prtc in proto:
                gxid = getChildNodesByName(prtc, u"Address")
                for ok in gxid:
                    ext = ok.getAttribute(u"Extended")
                    if ext == "1":
                        xid_add = ok.getAttribute(u"Xid")
                        strHex = "%0.2X" % int(address)
                        dictionary[strHex] = xid_add
                        break
    return dictionary


def convertXML():
    options.ecus_dir = "./ecus"

    ecus = glob.glob("ecus/*.xml")
    ecus.remove("ecus/eculist.xml")
    i = 1

    print(_("Opening ECU Database..."))
    ecu_database = EcuDatabase()
    print(_("Starting conversion"))

    for target in ecus:
        filename = target.replace(".xml", ".json")
        filename = filename.replace("ecus/", "json/")
        print(_("Starting processing ") + target + " " + str(i) + "/" + str(len(ecus)) + _(" to ") + filename)

        i += 1
        layoutjs = dumpXML(target)
        if layoutjs is None:
            print(_("Skipping current file (cannot parse it)"))
            continue
        ecufile = EcuFile(target, True)
        js = ecufile.dumpJson()

        if js:
            jsfile = open(filename, "w")
            jsfile.write(js)
            jsfile.close()

        if layoutjs:
            jsfile = open(filename + ".layout", "w")
            jsfile.write(layoutjs)
            jsfile.close()

        target_name = filename + ".targets"
        ecu_ident = ecu_database.getTargets(ecufile.ecuname)

        js_targets = []
        for ecui in ecu_ident:
            js_targets.append(ecui.dump())

        js = json.dumps(js_targets, indent=1)
        if js:
            jsfile = open(target_name, "w")
            jsfile.write(js)
            jsfile.close()


def dumpVehicles(file=os.path.join("vehicles", "projects.xml")):
    xdom = xml.dom.minidom.parse(file)
    xdoc = xdom.documentElement
    dictionary = {}
    projects_list = []
    projects_str = "<Projects>"
    dictionary["projects"] = {}
    dictionary["projects"]["All"] = {}
    dictionary["projects"]["All"]["DoIP"] = {}
    dictionary["projects"]["All"]["code"] = "ALL"
    dictionary["projects"]["All"]["addressing"] = dumpAddressing(os.path.join("vehicles", "GenericAddressing.xml"))
    dictionary["projects"]["All"]["snat"] = dumpSNAT(os.path.join("vehicles", "GenericAddressing.xml"))
    dictionary["projects"]["All"]["snat_ext"] = dumpSNAT_ext(os.path.join("vehicles", "GenericAddressing.xml"))
    dictionary["projects"]["All"]["dnat"] = dumpDNAT(os.path.join("vehicles", "GenericAddressing.xml"))
    dictionary["projects"]["All"]["dnat_ext"] = dumpDNAT_ext(os.path.join("vehicles", "GenericAddressing.xml"))
    manufacturers = getChildNodesByName(xdoc, u"Manufacturer")
    for manufacturer in manufacturers:
        name = str(manufacturer.getElementsByTagName(u"name")[0].childNodes[0].nodeValue).lower().title()
        projects = getChildNodesByName(manufacturer, u"project")
        for project in projects:
            protocols = getChildNodesByName(project, u"ProtocolList")
            for protocol in protocols:
                proto = getChildNodesByName(protocol, u"Protocol")
                for prtc in proto:
                    test = prtc.getAttribute(u"Name")
                    if test == "DoIP":
                        fcts = getChildNodesByName(prtc, u"Fct")
                        for fct in fcts:
                            #print(fct.getAttribute(u"Name"))
                            #print(int(fct.getAttribute(u"Value"), 16))
                            add_doip = int(fct.getAttribute(u"Value"), 16)
                            name_doip = fct.getAttribute(u"Name")
                            dictionary["projects"]["All"]["DoIP"][add_doip] = name_doip
            code = project.getAttribute(u"code")
            p_name = project.getAttribute(u"name")
            addressing = os.path.join("vehicles", "GenericAddressing.xml")
            parts = []
            try:
                parts = str(project.getElementsByTagName(u"addressing")[0].childNodes[0].nodeValue).split('/')
            except Exception:
                pass
            if len(parts) == 0:
                addressing = os.path.join("vehicles", "GenericAddressing.xml")
            elif len(parts) == 2:
                addressing = os.path.join("vehicles", parts[0], parts[1])
            elif len(parts) == 3:
                addressing = os.path.join("vehicles", parts[0], parts[1], parts[2])
            elif len(parts) == 4:
                addressing = os.path.join("vehicles", parts[0], parts[1], parts[2], parts[3])
            elif len(parts) > 4:
                print(_("parts as: ") + len(parts) + _(" please review dumpVehicles def."))
                addressing = os.path.join("vehicles", "GenericAddressing.xml")
            else:
                raise "Error in dumpVehicles def."
            if not os.path.isfile(addressing):
                addressing = os.path.join("vehicles", "GenericAddressing.xml")

            project_name = "[%s] - %s %s" % (str(code).upper(), name, p_name)

            dictionary["projects"][project_name] = {}
            dictionary["projects"][project_name]["code"] = str(code).upper()
            dictionary["projects"][project_name]["addressing"] = dumpAddressing(addressing)
            dictionary["projects"][project_name]["snat"] = dumpSNAT(addressing)
            dictionary["projects"][project_name]["snat_ext"] = dumpSNAT_ext(addressing)
            dictionary["projects"][project_name]["dnat"] = dumpDNAT(addressing)
            dictionary["projects"][project_name]["dnat_ext"] = dumpDNAT_ext(addressing)
            print(f'{code:18} => {addressing:40} => OK')
            projects_list.append(code)

    sd = sorted(dictionary["projects"].items())
    new_dict = {"projects": {}}
    for k, v in sd:
        new_dict["projects"][k] = v
    # js = json.dumps(new_dict, ensure_ascii=False, indent=True)
    js = json.dumps(new_dict, ensure_ascii=False)
    f = open(os.path.join(get_dir("src"), "ddt4all", "resources", "projects.json"), "w", encoding="UTF-8")
    f.write(js)
    f.close()
    for p in sorted(projects_list, key=str.casefold):
        projects_str += f'<{p}/>'
    projects_str += "</Projects>"
    print(projects_str)
