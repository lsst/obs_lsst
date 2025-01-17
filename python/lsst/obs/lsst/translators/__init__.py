# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

from .lsstCam import *
from .phosim import *
from .ts3 import *
from .ts8 import *
from .imsim import *
from .latiss import *
from .lsst_ucdcam import *
from .comCam import *
from .comCamSim import *
from .lsstCamSim import *


def _register_translators() -> list[str]:
    """Ensure that the translators are loaded.

    When this function is imported we are guaranteed to also import the
    translators which will automatically register themselves.

    Returns
    -------
    translators : `list` [ `str` ]
        The names of the translators provided by this package.
    """
    return [
        LsstCamTranslator.name,
        LatissTranslator.name,
        LsstComCamTranslator.name,
        LsstComCamSimTranslator.name,
        LsstCamSimTranslator.name,
        LsstCamImSimTranslator.name,
        LsstUCDCamTranslator.name,
        LsstCamPhoSimTranslator.name,
    ]
