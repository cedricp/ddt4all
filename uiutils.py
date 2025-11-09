#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys

import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets

import options

_ = options.translator('ddt4all')


def getChildNodesByName(parent, name):
    nodes = []
    for node in parent.childNodes:
        if node.nodeType == node.ELEMENT_NODE and node.localName == name:
            nodes.append(node)
    return nodes


def colorConvert(color):
    hexcolor = hex(int(color) & 0xFFFFFF)[2:].upper().zfill(6)
    redcolor = int('0x' + hexcolor[0:2], 16)
    greencolor = int('0x' + hexcolor[2:4], 16)
    bluecolor = int('0x' + hexcolor[4:6], 16)
    return 'rgb(%i,%i,%i)' % (bluecolor, greencolor, redcolor)


def getRectangleXML(xml, scale=1):
    rect = {}
    rect['left'] = int(float(xml.getAttribute("Left")) / float(scale))
    rect['top'] = int(float(xml.getAttribute("Top")) / float(scale))
    rect['height'] = int(float(xml.getAttribute("Height")) / float(scale))
    rect['width'] = int(float(xml.getAttribute("Width")) / float(scale))
    return rect


def getFontColor(xml):
    font = getChildNodesByName(xml, "Font")[0]
    if font.getAttribute("Color"):
        return colorConvert(font.getAttribute("Color"))
    else:
        return colorConvert(0xAAAAAA)


def getFontXML(xml):
    f = {}
    font = getChildNodesByName(xml, "Font")[0]
    f['name'] = font.getAttribute("Name")
    f['size'] = float(font.getAttribute("Size").replace(',', '.'))
    f['bold'] = font.getAttribute("Bold")
    f['italic'] = font.getAttribute("Italic")
    return f


def getXMLFont(xml, scale=1):
    font = getChildNodesByName(xml, "Font")[0]
    font_name = font.getAttribute("Name")
    font_size = float(font.getAttribute("Size").replace(',', '.'))
    if sys.platform[:3] == "dar":
        font_name = "Arial"
        font_size = 11
    font_bold = font.getAttribute("Bold")
    font_italic = font.getAttribute("Italic")

    if font_bold == '1':
        fnt_flags = gui.QFont.Bold
    else:
        fnt_flags = gui.QFont.Normal

    if font_italic == '1':
        fnt_flags |= gui.QFont.StyleItalic

    font_size: float = font_size / float(scale) * 14.
    qfnt = gui.QFont(font_name, int(font_size), fnt_flags)
    qfnt.setPixelSize(int(font_size))
    return qfnt


class displayData:
    def __init__(self, data, widget, is_combo=False):
        self.data = data
        self.widget = widget
        self.is_combo = is_combo


class displayDict:
    def __init__(self, request_name, request):
        self.request = request
        self.request_name = request_name
        self.data = []
        self.datadict = {}

    def addData(self, displaydata):
        self.data.append(displaydata)
        if not displaydata.data.name in self.datadict:
            self.datadict[displaydata.data.name] = displaydata

    def getDataByName(self, name):
        for data in self.data:
            if data.data.name == name:
                return data
        return None


def jsonFont(fnt, scale):
    font_name = fnt['name']
    font_size = fnt['size']
    if sys.platform[:3] == "dar":
        font_name = "Arial"
        font_size = 11
    if 'bold' in fnt:
        font_bold = fnt['bold']
    else:
        font_bold = '0'
    if 'italic' in fnt:
        font_italic = fnt['italic']
    else:
        font_italic = '0'

    if font_bold == '1':
        fnt_flags = gui.QFont.Bold
    else:
        fnt_flags = gui.QFont.Normal

    if font_italic == '1':
        fnt_flags |= gui.QFont.StyleItalic

    font_size = int(font_size / float(scale) * 14.)

    qfnt = gui.QFont(font_name, font_size, fnt_flags)
    qfnt.setPixelSize(font_size)
    return qfnt


# ============================================================================
# Common utility functions
# ============================================================================

def show_message_box(title, text, icon_type=widgets.QMessageBox.Information, 
                     informative_text=None, parent=None):
    """
    Centralized message box creation with consistent styling
    
    Args:
        title: Window title
        text: Main message text
        icon_type: QMessageBox icon type
        informative_text: Optional additional information
        parent: Parent widget
        
    Returns:
        Result of exec_()
    """
    msgbox = widgets.QMessageBox(parent)
    app_icon = gui.QIcon("ddt4all_data/icons/obd.png")
    msgbox.setWindowIcon(app_icon)
    msgbox.setWindowTitle(title)
    msgbox.setIcon(icon_type)
    msgbox.setText(text)
    
    if informative_text:
        msgbox.setInformativeText(informative_text)
    
    return msgbox.exec_()


def get_app_icon():
    """Get the standard application icon"""
    return gui.QIcon("ddt4all_data/icons/obd.png")


# Device keyword mapping for cleaner device detection
DEVICE_KEYWORDS = {
    'ELS27': 'ELS27 V5 Compatible',
    'ELM327': 'ELM327 Compatible',
    'VLINKER': 'Vlinker Compatible',
    'OBDII': 'Vlinker Compatible',
    'VGATE': 'VGate Compatible',
    'ICAR': 'VGate Compatible',
    'OBDLINK': 'OBDLink Compatible',
    'SCANTOOL': 'OBDLink Compatible',
}

# USB chip detection for device identification
USB_CHIP_KEYWORDS = {
    'FTDI': 'FTDI - Possible ELS27/ELM327',
    'FT232': 'FTDI - Possible ELS27/ELM327',
    'FT231X': 'FTDI - Possible ELS27/ELM327',
    'CH340': 'CH340 - Possible ELS27/ELM327',
    'CH341': 'CH340 - Possible ELS27/ELM327',
    'CP210': 'CP210x - Possible ELS27/ELM327',
    'CP2102': 'CP210x - Possible ELS27/ELM327',
    'CP2104': 'CP210x - Possible ELS27/ELM327',
    'PL2303': 'PL2303 - Possible ELS27/ELM327',
}


def get_device_description(desc):
    """
    Get enhanced device description based on keywords
    
    Args:
        desc: Original device description
        
    Returns:
        Enhanced description with device type
    """
    desc_upper = desc.upper()
    
    # Check direct device names first
    for keyword, label in DEVICE_KEYWORDS.items():
        if keyword in desc_upper:
            return f"{desc} ({label})"
    
    # Check USB chip types
    for chip, label in USB_CHIP_KEYWORDS.items():
        if chip in desc_upper:
            return f"{desc} ({label})"
    
    return desc


class ExponentialBackoff:
    """
    Exponential backoff for retry operations
    """
    def __init__(self, base_delay=1.0, max_delay=16.0, max_retries=5):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.current_retry = 0
        
    def get_delay(self):
        """Get current delay value"""
        if self.current_retry >= self.max_retries:
            return None
        
        delay = min(self.base_delay * (2 ** self.current_retry), self.max_delay)
        self.current_retry += 1
        return delay
    
    def reset(self):
        """Reset retry counter"""
        self.current_retry = 0
        
    @property
    def can_retry(self):
        """Check if more retries are available"""
        return self.current_retry < self.max_retries


def safe_int_convert(value, default=0):
    """
    Safely convert value to int with default fallback
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float_convert(value, default=0.0):
    """
    Safely convert value to float with default fallback
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def clamp(value, min_value, max_value):
    """
    Clamp value between min and max
    
    Args:
        value: Value to clamp
        min_value: Minimum value
        max_value: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_value, min(value, max_value))
