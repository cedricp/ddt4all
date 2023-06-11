#!/usr/bin/python3
# -*- coding: utf-8 -*-
import glob
import os
import sys
import zipfile

import options
import version

__author__ = version.__author__
__copyright__ = version.__copyright__
__credits__ = version.__credits__
__license__ = version.__license__
__version__ = version.__version__
__maintainer__ = version.__maintainer__
__email__ = version.__email__
__status__ = version.__status__

_ = options.translator('ddt4all')


def zipdir(dirname):
    for root, dirs, files in os.walk(dirname, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            if ".pyc" in filename or ".DS_Store" in filename:
                continue
            print("Adding source file %s" % filename)
            zip.write(filename)


if not os.path.exists("./Output"):
    os.mkdir("./Output")

default_file = "ddt4all.zip"

if sys.platform[:3] == "win":
    default_file = "ddt4all_windows.zip"
elif sys.platform[:3] == "dar":
    default_file = "ddt4all_macos.zip"
elif sys.platform[:3] == "lin":
    default_file = "ddt4all_linux.zip"

zip = zipfile.ZipFile("./Output/" + default_file, mode="w", compression=zipfile.ZIP_DEFLATED, allowZip64=True)
files = glob.glob("*.py")

for file in files:
    print(_("Adding source file %s") % file)
    zip.write(file)

files = glob.glob("./ddtplugins/*.py")
for file in files:
    print(_("Adding plugin file %s") % file)
    zip.write(file)

if os.path.exists('./ecu.zip'):
    zip.write("./ecu.zip")

if sys.platform[:3] == "win":
    zip.write("./DDT4ALL.BAT")
else:
    zip.write("./ddt4all.sh")

zip.write("./requirements.txt")
# Need a real python installation
# zipdir("./venv")
zipdir("./icons")
zipdir("./address")
zipdir("./json")
zipdir("./locale")

zip.close()
