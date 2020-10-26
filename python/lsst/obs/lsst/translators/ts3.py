# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for LSST BNL TestStand 3 headers"""

__all__ = ("LsstTS3Translator", )

import logging
import re
import os.path

import astropy.units as u
from astropy.time import Time, TimeDelta

from astro_metadata_translator import cache_translation

from .lsst import LsstBaseTranslator

log = logging.getLogger(__name__)

# There is only a single sensor at a time so define a
# fixed sensor name
_DETECTOR_NAME = "S00"


class LsstTS3Translator(LsstBaseTranslator):
    """Metadata translator for LSST BNL Test Stand 3 data.
    """

    name = "LSST-TS3"
    """Name of this translation class"""

    _const_map = {
        # TS3 is not attached to a telescope so many translations are null.
        "instrument": "LSST-TS3",
        "telescope": None,
        "location": None,
        "boresight_rotation_coord": None,
        "boresight_rotation_angle": None,
        "boresight_airmass": None,
        "tracking_radec": None,
        "altaz_begin": None,
        "object": "UNKNOWN",
        "relative_humidity": None,
        "temperature": None,
        "pressure": None,
        "detector_name": _DETECTOR_NAME,  # Single sensor
    }

    _trivial_map = {
        "detector_serial": "LSST_NUM",
        "physical_filter": "FILTER",
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
    }

    DETECTOR_NAME = _DETECTOR_NAME
    """Fixed name of single sensor."""

    DETECTOR_MAX = 999
    """Maximum number of detectors to use when calculating the
    detector_exposure_id."""

    cameraPolicyFile = "policy/ts3.yaml"

    _ROLLOVER_TIME = TimeDelta(8*60*60, scale="tai", format="sec")
    """Time delta for the definition of a Rubin Test Stand start of day."""

    @classmethod
    def can_translate(cls, header, filename=None):
        """Indicate whether this translation class can translate the
        supplied header.

        There is no usable ``INSTRUME`` header in TS3 data. Instead we use
        the ``TSTAND`` header.

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
        return cls.can_translate_with_options(header, {"TSTAND": "BNL-TS3-2-Janeway"}, filename=filename)

    @staticmethod
    def compute_exposure_id(dateobs, seqnum=0, controller=None):
        """Helper method to calculate the TS3 exposure_id.

        Parameters
        ----------
        dateobs : `str`
            Date of observation in FITS ISO format.
        seqnum : `int`, unused
            Sequence number. Ignored.
        controller : `str`, unused
            Controller type. Ignored.

        Returns
        -------
        exposure_id : `int`
            Exposure ID.
        """
        # There is worry that seconds are too coarse so use 10th of second
        # and read the first 21 characters.
        exposure_id = re.sub(r"\D", "", dateobs[:21])
        return int(exposure_id)

    @cache_translation
    def to_datetime_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        self._used_these_cards("MJD-OBS")
        return Time(self._header["MJD-OBS"], scale="utc", format="mjd")

    def to_exposure_id(self):
        """Generate a unique exposure ID number

        Note that SEQNUM is not unique for a given day in TS3 data
        so instead we convert the ISO date of observation directly to an
        integer.

        Returns
        -------
        exposure_id : `int`
            Unique exposure number.
        """
        iso = self._header["DATE-OBS"]
        self._used_these_cards("DATE-OBS")

        return self.compute_exposure_id(iso)

    # For now assume that visit IDs and exposure IDs are identical
    to_visit_id = to_exposure_id

    @cache_translation
    def to_science_program(self):
        """Calculate the science program information.

        There is no header recording this in TS3 data so instead return
        the observing day in YYYY-MM-DD format.

        Returns
        -------
        run : `str`
            Observing day in YYYY-MM-DD format.
        """
        # Get a copy so that we can edit the default formatting
        date = self.to_datetime_begin().copy()
        date.format = "iso"
        date.out_subfmt = "date"  # YYYY-MM-DD format
        return str(date)

    @cache_translation
    def to_observation_id(self):
        # Docstring will be inherited. Property defined in properties.py
        filename = self._header["FILENAME"]
        self._used_these_cards("FILENAME")
        return os.path.splitext(filename)[0]

    @cache_translation
    def to_detector_group(self):
        # Docstring will be inherited. Property defined in properties.py
        serial = self.to_detector_serial()
        detector_info = self.compute_detector_info_from_serial(serial)
        return detector_info[0]
