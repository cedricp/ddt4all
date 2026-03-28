import argparse

from ddt4all.core.parameters.helpers import (
    zipConvertXML,
    convertXML,
    dumpVehicles
)

def cmd_parameters(args: argparse.Namespace) -> int:

    if args.zipconvert:
        zipConvertXML()

    if args.convert:
        convertXML()

    if args.dumpprojects:
        dumpVehicles()