# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for the Simulated LSST Commissioning Camera"""

__all__ = ("LsstComCamSimTranslator", )

import logging

from .lsstCam import LsstCamTranslator
from .lsst import SIMONYI_TELESCOPE

log = logging.getLogger(__name__)


class LsstComCamSimTranslator(LsstCamTranslator):
    """Metadata translation for the LSST Commissioning Camera."""

    name = "LSSTComCamSim"
    """Name of this translation class"""

    _const_map = {
        "instrument": "LSSTComCamSim",
    }

    cameraPolicyFile = 'policy/comCamSim.yaml'

    @classmethod
    def can_translate(cls, header, filename=None):
        """Indicate whether this translation class can translate the
        supplied header.

        Looks for "COMCAMSIM" instrument in case-insensitive manner but
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
            if instrument == "comcamsim" and telescope in (SIMONYI_TELESCOPE, "LSST"):
                return True
            telcode = header.get("TELCODE", None)
            # Some lab data reports that it is LSST_CAMERA
            if telcode == "CC" and telescope in (SIMONYI_TELESCOPE, "LSST"):
                return True

        return False

    @classmethod
    def fix_header(cls, header, instrument, obsid, filename=None):
        """Fix Simulated ComCam headers.

        Notes
        -----
        Content will be added as needed.

        Corrections are reported as debug level log messages.

        See `~astro_metadata_translator.fix_header` for details of the general
        process.
        """
        modified = False

        return modified

    def _is_on_mountain(self):
        """Indicate whether these data are coming from the instrument
        installed on the mountain.
        Returns
        -------
        is : `bool`
            `True` if instrument is on the mountain.

        Notes
        -----
        TODO: DM-33387 This is currently a terrible hack and MUST be removed
        once CAP-807 and CAP-808 are done.
        Until then, ALL non-calib ComCam data will look like it is on sky.
        """
        return True