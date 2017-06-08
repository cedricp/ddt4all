#!/usr/bin/python

import os, zipfile, glob


def zipdir(dirname):
    for root, dirs, files in os.walk(dirname, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            if ".pyc" in filename:
                continue
            print "Adding source file %s" % filename
            zip.write(filename)

zip = zipfile.ZipFile("ddt4all_windows.zip", mode="w", compression=zipfile.ZIP_DEFLATED, allowZip64=True)
files = glob.glob("*.py")
for file in files:
    print "Adding source file %s" % file
    zip.write(file)

zip.write("DDT4ALL.BAT")
zip.write("json/")

zipdir("./Python27")
zipdir("./importlib")
zipdir("./serial")
zipdir("./icons")
zipdir("./json")


zip.write("logs/")
zip.write("ecus/")

zip.close()