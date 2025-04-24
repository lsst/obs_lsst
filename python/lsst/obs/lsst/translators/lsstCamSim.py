# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for the Simulated LSST Camera"""

__all__ = ("LsstCamSimTranslator",)

import logging
import astropy

from astro_metadata_translator import cache_translation

from .lsstCam import LsstCamTranslator
from .lsst import SIMONYI_TELESCOPE

log = logging.getLogger(__name__)


class LsstCamSimTranslator(LsstCamTranslator):
    """Metadata translation for the simulated LSST Camera."""

    name = "LSSTCamSim"
    """Name of this translation class"""

    _const_map = {
        "instrument": "LSSTCamSim",
        "has_simulated_content": True,
    }

    cameraPolicyFile = "policy/lsstCamSim.yaml"

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
        if "INSTRUME" in header and "TELESCOP" in header:
            telescope = header["TELESCOP"]
            instrument = header["INSTRUME"].lower()
            if instrument == "lsstcamsim" and telescope in (SIMONYI_TELESCOPE, "LSST"):
                return True

        return False

    @classmethod
    def fix_header(cls, header, instrument, obsid, filename=None):
        """Fix Simulated LSSTCamSim headers.

        Notes
        -----
        Content will be added as needed.

        Corrections are reported as debug level log messages.

        See `~astro_metadata_translator.fix_header` for details of the general
        process.
        """
        modified = False

        # Currently, no fixes are required.

        return modified

    @classmethod
    def observing_date_to_offset(cls, observing_date: astropy.time.Time) -> astropy.time.TimeDelta | None:
        # Always use the 12 hour offset.
        return cls._ROLLOVER_TIME

    def _is_on_mountain(self):
        """Indicate whether these data are coming from the instrument
        installed on the mountain.

        Returns
        -------
        is : `bool`
            `True` if instrument is on the mountain.

        Notes
        -----
        Simulated LSSTCam is always on the mountain.
        """
        return True

    @cache_translation
    def to_altaz_end(self):
        # Tries to calculate the value. Simulated files for ops-rehearsal 3
        # did not have the AZ/EL headers defined.
        if self.are_keys_ok(["ELEND", "AZEND"]):
            return super().to_altaz_end()
        # Do not attempt to calculate anything in this situation since it is
        # never going to be correct.
        return None
