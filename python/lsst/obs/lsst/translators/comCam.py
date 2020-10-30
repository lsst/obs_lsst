# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for the LSST Commissioning Camera"""

__all__ = ("LsstComCamTranslator", )

import logging

from .lsstCam import LsstCamTranslator
from .lsst import SIMONYI_TELESCOPE

log = logging.getLogger(__name__)

DETECTOR_SERIALS = {
    "S00": "ITL-3800C-229",
    "S01": "ITL-3800C-251",
    "S02": "ITL-3800C-215",
    "S10": "ITL-3800C-326",
    "S11": "ITL-3800C-283",
    "S12": "ITL-3800C-243",
    "S20": "ITL-3800C-319",
    "S21": "ITL-3800C-209",
    "S22": "ITL-3800C-206",
}


class LsstComCamTranslator(LsstCamTranslator):
    """Metadata translation for the LSST Commissioning Camera."""

    name = "LSSTComCam"
    """Name of this translation class"""

    _const_map = {
        "instrument": "LSSTComCam",
    }

    # Use the comCam raft definition
    cameraPolicyFile = "policy/comCam.yaml"

    @classmethod
    def can_translate(cls, header, filename=None):
        """Indicate whether this translation class can translate the
        supplied header.

        Looks for "COMCAM" instrument in case-insensitive manner but
        must be on LSST telescope.  This avoids confusion with other
        telescopes using commissioning cameras.

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
        if "INSTRUME" in header and "TELESCOP" in header:
            telescope = header["TELESCOP"]
            instrument = header["INSTRUME"].lower()
            if instrument == "comcam" and telescope in (SIMONYI_TELESCOPE, "LSST"):
                return True
            telcode = header.get("TELCODE", None)
            # Some lab data reports that it is LSST_CAMERA
            if telcode == "CC" and telescope in (SIMONYI_TELESCOPE, "LSST"):
                return True

        return False

    @classmethod
    def fix_header(cls, header, instrument, obsid, filename=None):
        """Fix ComCam headers.

        Notes
        -----
        Fixes the following issues:

        * If LSST_NUM is missing it is filled in by looking at the CCDSLOT
          value and assuming that the ComCam detectors are fixed.

        Corrections are reported as debug level log messages.

        See `~astro_metadata_translator.fix_header` for details of the general
        process.
        """
        modified = False

        # Prefer filename to obsid for log messages
        log_label = filename or obsid

        if "LSST_NUM" not in header:
            slot = header.get("CCDSLOT", None)
            if slot in DETECTOR_SERIALS:
                header["LSST_NUM"] = DETECTOR_SERIALS[slot]
                modified = True
                log.debug("%s: Set LSST_NUM to %s", log_label, header["LSST_NUM"])

        return modified
