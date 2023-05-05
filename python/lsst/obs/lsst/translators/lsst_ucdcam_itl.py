# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for LSST UC Davis ITL Test Stand headers"""

__all__ = ("LsstUCDCamITLTranslator", )

import logging
import astropy.units as u

from .lsst import LsstBaseTranslator

log = logging.getLogger(__name__)


LSST_UCDCAM = "LSST-UCDCam-ITL"

DETECTOR_GROUP_NAME = "R22"

DETECTOR_NAME = "S01"


class LsstUCDCamITLTranslator(LsstBaseTranslator):
    """Metadata translator for LSST UC Davis ITL Test Stand."""

    name = LSST_UCDCAM
    """Name of this translation class."""

    supported_instrument = LSST_UCDCAM
    """Supports the LSST-UCDCam-ITL instrument."""

    _const_map = {
        "instrument": LSST_UCDCAM,
        "telescope": None,
        "location": None,
        "boresight_rotation_coord": None,
        "boresight_rotation_angle": None,
        "boresight_airmass": None,
        "tracking_radec": None,
        "altaz_begin": None,
        "object": "UNKNOWN",
        "detector_group": DETECTOR_GROUP_NAME,
        "detector_name": DETECTOR_NAME,
        "relative_humidity": None,
        "temperature": None,
        "pressure": None,
    }

    _trivial_map = {
        "observation_id": "OBSID",
        "detector_serial": "LSST_NUM",
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
        "science_program": ("RUNNUM", dict(default="unknown"))
    }

    @classmethod
    def can_translate(cls, header, filename=None):
        """Indicate whether this translation class can translate the
        supplied header.

        Parameters
        ----------
        header : `dict`-like
            Header to convert to standardized form.
        filename : `str`, optional
            Name of file being translated.
        Returns
        -------
        can : `bool`
            `True` if the header is recognized by this class. `False`
            otherwise.
        """
        if "INSTRUME" in header:
            instrume = header["INSTRUME"].lower()
            if instrume == cls.supported_instrument.lower():
                return True
        return False
