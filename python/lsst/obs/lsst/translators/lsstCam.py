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

from astro_metadata_translator import cache_translation
from astro_metadata_translator.translators.helpers import is_non_science

from .lsst import LsstBaseTranslator, SIMONYI_TELESCOPE, FILTER_DELIMITER

log = logging.getLogger(__name__)

# Normalized name of the LSST Camera
LSST_CAM = "LSSTCam"


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

    name = LSST_CAM
    """Name of this translation class"""

    supported_instrument = LSST_CAM
    """Supports the lsstCam instrument."""

    _const_map = {
        "instrument": LSST_CAM,
        "telescope": SIMONYI_TELESCOPE,
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

    @classmethod
    def fix_header(cls, header, instrument, obsid, filename=None):
        """Fix LSSTCam headers.

        Notes
        -----
        See `~astro_metadata_translator.fix_header` for details of the general
        process.
        """

        modified = False

        # Prefer filename to obsid for log messages
        log_label = filename or obsid

        if "FILTER" not in header and header.get("FILTER2") is not None:
            ccdslot = header.get("CCDSLOT", "unknown")
            raftbay = header.get("RAFTBAY", "unknown")

            log.warn("%s %s_%s: No FILTER key found but FILTER2=\"%s\" (removed)",
                     log_label, raftbay, ccdslot, header["FILTER2"])
            header["FILTER2"] = None
            modified = True

        return modified

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
        # INSTRUME keyword might be of two types
        if "INSTRUME" in header:
            instrume = header["INSTRUME"].lower()
            if instrume == cls.supported_instrument.lower():
                return True
        return False

    @cache_translation
    def to_physical_filter(self):
        """Calculate the physical filter name.

        Returns
        -------
        filter : `str`
            Name of filter. Can be a combination of FILTER and FILTER2
            headers joined by a "~" if FILTER2 is set and not empty.
            Returns "UNKNOWN" if no filter is declared.
        """
        physical_filter = self._determine_primary_filter()

        filter2 = None
        if self.is_key_ok("FILTER2"):
            self._used_these_cards("FILTER2")
            filter2 = self._header["FILTER2"]
            if self._is_filter_empty(filter2):
                filter2 = None

        if filter2:
            physical_filter = f"{physical_filter}{FILTER_DELIMITER}{filter2}"

        return physical_filter
