# This directory contains the translator plugins for the
# astro_metadata_translator package.  The plugins follow the coding
# style of astro_metadata_translator rather than the coding style
# of obs_lsst.  The intent is for these plugins to be transferrable
# out of this package and integrated into astro_metadata_translator when
# they become stable.

from .phosim import *
from .ts8 import *
from .imsim import *
from .auxTel import *
