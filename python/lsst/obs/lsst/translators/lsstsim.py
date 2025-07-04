# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for LSST simulations"""

__all__ = ("LsstSimTranslator", )

import warnings
import logging

import astropy.utils.exceptions
from astropy.coordinates import AltAz
from astro_metadata_translator import cache_translation

from .lsst import (
    LsstBaseTranslator,
    SIMONYI_LOCATION,
    SIMONYI_TELESCOPE,
    compute_detector_exposure_id_generic,
)

log = logging.getLogger(__name__)


class LsstSimTranslator(LsstBaseTranslator):
    """Shared routines for LSST Simulated Data.
    """

    # Reset mappings
    _const_map = {
        # neither phosim nor imsim report a counter
        "observation_counter": 0,
        "has_simulated_content": True,
    }
    _trivial_map = {}

    @classmethod
    def max_exposure_id(cls):
        """The maximum exposure ID expected from this instrument.

        Returns
        -------
        max_exposure_id : `int`
            The maximum value.
        """
        return 9_999_999

    @classmethod
    def compute_detector_exposure_id(cls, exposure_id, detector_num):
        # Docstring inherited from LsstBaseTranslator.
        return compute_detector_exposure_id_generic(exposure_id, detector_num, max_num=cls.DETECTOR_MAX)

    @cache_translation
    def to_telescope(self):
        # Docstring will be inherited. Property defined in properties.py
        telescope = None
        if self.is_key_ok("OUTFILE") and self._header["OUTFILE"].startswith("lsst"):
            telescope = SIMONYI_TELESCOPE
            self._used_these_cards("OUTFILE")
        elif "LSST_NUM" in self._header:
            telescope = SIMONYI_TELESCOPE
            self._used_these_cards("LSST_NUM")
        return telescope

    @cache_translation
    def to_location(self):
        # Docstring will be inherited. Property defined in properties.py
        location = None
        # In theory simulated files might not be for LSST
        tel = self.to_telescope()
        if tel == SIMONYI_TELESCOPE:
            location = SIMONYI_LOCATION
        else:
            # Try standard FITS headers
            try:
                location = super().to_location()
            except Exception:
                pass
        return location

    @cache_translation
    def to_altaz_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        if self.to_observation_type() == "science":
            # Derive from RADec in absence of any other information
            radec = self.to_tracking_radec()
            if radec is not None:
                # This can trigger warnings because of the future dates
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=astropy.utils.exceptions.AstropyWarning)
                    altaz = radec.transform_to(AltAz())
                return altaz
        return None

    @cache_translation
    def to_altaz_end(self):
        # imsim and phosim do not have this information and we make no attempt
        # to calculate it from the tracking radec and exposure end time.
        return None
