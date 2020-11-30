try:
    from crcmod.crcmod import *
except ImportError:
    # Make this backward compatible
    from crcmod import *
__doc__ = crcmod.__doc__
