#-----------------------------------------------------------------------------
# Copyright (c) 2010 Craig McQueen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#-----------------------------------------------------------------------------
'''
crcmod.predefined defines some well-known CRC algorithms.

To use it, e.g.:
    import crcmod.predefined
    
    crc32func = crcmod.predefined.mkPredefinedCrcFun("crc-32")
    crc32class = crcmod.predefined.PredefinedCrc("crc-32")

crcmod.predefined.Crc is an alias for crcmod.predefined.PredefinedCrc
But if doing 'from crc.predefined import *', only PredefinedCrc is imported.
'''

# local imports
import crcmod

__all__ = [
    'PredefinedCrc',
    'mkPredefinedCrcFun',
]

REVERSE = True
NON_REVERSE = False

# The following table defines the parameters of well-known CRC algorithms.
# The "Check" value is the CRC for the ASCII byte sequence b"123456789". It
# can be used for unit tests.
_crc_definitions_table = [
#       Name                Identifier-name,    Poly            Reverse         Init-value      XOR-out     Check
    [   'crc-8',            'Crc8',             0x107,          NON_REVERSE,    0x00,           0x00,       0xF4,       ],

    [   'crc-16',           'Crc16',            0x18005,        REVERSE,        0x0000,         0x0000,     0xBB3D,     ],
    [   'crc-16-usb',       'Crc16Usb',         0x18005,        REVERSE,        0x0000,         0xFFFF,     0xB4C8,     ],
    [   'x-25',             'CrcX25',           0x11021,        REVERSE,        0x0000,         0xFFFF,     0x906E,     ],
    [   'xmodem',           'CrcXmodem',        0x11021,        NON_REVERSE,    0x0000,         0x0000,     0x31C3,     ],
    [   'modbus',           'CrcModbus',        0x18005,        REVERSE,        0xFFFF,         0x0000,     0x4B37,     ],

    # Note definitions of CCITT are disputable. See:
    #    http://homepages.tesco.net/~rainstorm/crc-catalogue.htm
    #    http://web.archive.org/web/20071229021252/http://www.joegeluso.com/software/articles/ccitt.htm
    [   'kermit',           'CrcKermit',        0x11021,        REVERSE,        0x0000,         0x0000,     0x2189,     ],
    [   'crc-ccitt-false',  'CrcCcittFalse',    0x11021,        NON_REVERSE,    0xFFFF,         0x0000,     0x29B1,     ],
    [   'crc-aug-ccitt',    'CrcAugCcitt',      0x11021,        NON_REVERSE,    0x1D0F,         0x0000,     0xE5CC,     ],

    [   'crc-24',           'Crc24',            0x1864CFB,      NON_REVERSE,    0xB704CE,       0x000000,   0x21CF02,   ],

    [   'crc-32',           'Crc32',            0x104c11db7,    REVERSE,        0x00000000,     0xFFFFFFFF, 0xCBF43926, ],
    [   'crc-32c',          'Crc32C',           0x11edc6f41,    REVERSE,        0x00000000,     0xFFFFFFFF, 0xE3069283, ],
    [   'crc-32-mpeg',      'Crc32Mpeg',        0x104c11db7,    NON_REVERSE,    0xFFFFFFFF,     0x00000000, 0x0376E6E7, ],
    [   'posix',            'CrcPosix',         0x104c11db7,    NON_REVERSE,    0xFFFFFFFF,     0xFFFFFFFF, 0x765E7680, ],

# 64-bit
#       Name                Identifier-name,    Poly                    Reverse         Init-value          XOR-out             Check
    [   'crc-64',           'Crc64',            0x1000000000000001B,    REVERSE,        0x0000000000000000, 0x0000000000000000, 0x46A5A9388A5BEFFE, ],
    [   'crc-64-jones',     'Crc64Jones',       0x1ad93d23594c935a9,    REVERSE,        0x0000000000000000, 0x0000000000000000, 0xE9C6D914C4B8D9CA, ],
]


def _simplify_name(name):
    """
    Reduce CRC definition name to a simplified form:
        * lowercase
        * dashes removed
        * spaces removed
        * any initial "CRC" string removed
    """
    name = name.lower()
    name = name.replace('-', '')
    name = name.replace(' ', '')
    if name.startswith('crc'):
        name = name[len('crc'):]
    return name


_crc_definitions_by_name = {}
_crc_definitions_by_identifier = {}
_crc_definitions = []

_crc_table_headings = [ 'name', 'identifier', 'poly', 'reverse', 'init', 'xor_out', 'check' ]

for table_entry in _crc_definitions_table:
    crc_definition = dict(zip(_crc_table_headings, table_entry))
    _crc_definitions.append(crc_definition)
    name = _simplify_name(table_entry[0])
    if name in _crc_definitions_by_name:
        raise Exception("Duplicate entry for '{0}' in CRC table".format(name))
    _crc_definitions_by_name[name] = crc_definition
    _crc_definitions_by_identifier[table_entry[1]] = crc_definition


def _get_definition_by_name(crc_name):
    definition = _crc_definitions_by_name.get(_simplify_name(crc_name), None)
    if not definition:
        definition = _crc_definitions_by_identifier.get(crc_name, None)
    if not definition:
        raise KeyError("Unkown CRC name '{0}'".format(crc_name))
    return definition


class PredefinedCrc(crcmod.Crc):
    def __init__(self, crc_name):
        definition = _get_definition_by_name(crc_name)
        super().__init__(poly=definition['poly'], initCrc=definition['init'], rev=definition['reverse'], xorOut=definition['xor_out'])


# crcmod.predefined.Crc is an alias for crcmod.predefined.PredefinedCrc
Crc = PredefinedCrc


def mkPredefinedCrcFun(crc_name):
    definition = _get_definition_by_name(crc_name)
    return crcmod.mkCrcFun(poly=definition['poly'], initCrc=definition['init'], rev=definition['reverse'], xorOut=definition['xor_out'])


# crcmod.predefined.mkCrcFun is an alias for crcmod.predefined.mkPredefinedCrcFun
mkCrcFun = mkPredefinedCrcFun
