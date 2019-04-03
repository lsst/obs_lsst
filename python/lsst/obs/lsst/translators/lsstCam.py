# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for the main LSST Camera"""

__all__ = ("LsstCamTranslator", )

import logging
import astropy.units as u

# from astro_metadata_translator import cache_translation
from astro_metadata_translator.translators.helpers import is_non_science

from .lsst import LsstBaseTranslator

log = logging.getLogger(__name__)


def is_non_science_or_lab(self):
    """Pseudo method to determine whether this is a lab or non-science
    header.

    Raises
    ------
    KeyError
        If this is a science observation and on the mountain.
    """
    if is_non_science(self):
        return
    if not self._is_on_mountain():
        return
    raise KeyError("Required key is missing and this is a mountain science observation")


class LsstCamTranslator(LsstBaseTranslator):
    """Metadata translation for the main LSST Camera."""

    name = "LSSTCam"
    """Name of this translation class"""

    supported_instrument = "lsstCam"
    """Supports the lsstCam instrument."""

    _const_map = {
        "telescope": "LSST",
        # Migrate these to full translations once test data appears that
        # includes them
        "boresight_rotation_coord": "unknown",
        "boresight_rotation_angle": None,
        "boresight_airmass": None,
        "tracking_radec": None,
        "altaz_begin": None,
        "object": "UNKNOWN",
        "relative_humidity": None,
        "temperature": None,
        "pressure": None,
    }

    _trivial_map = {
        "detector_group": "RAFTBAY",
        "detector_name": "CCDSLOT",
        "observation_id": "OBSID",
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
        "detector_serial": "LSST_NUM",
        "science_program": ("RUNNUM", dict(default="unknown"))
    }

    # Use Imsim raft definitions until a true lsstCam definition exists
    cameraPolicyFile = "policy/lsstCam.yaml"
