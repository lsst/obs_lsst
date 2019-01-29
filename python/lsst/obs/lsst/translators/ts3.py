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
from astropy.time import Time

from astro_metadata_translator import cache_translation, StubTranslator

log = logging.getLogger(__name__)

# Define the group name for TS8 globally so that it can be used
# in multiple places. There is only a single sensor so define a
# raft for consistency with other LSST cameras.
_DETECTOR_GROUP_NAME = "RXX"
_DETECTOR_NAME = "S00"


class LsstTS3Translator(StubTranslator):
    """Metadata translator for LSST BNL Test Stand 3 data.
    """

    name = "LSST-TS3"
    """Name of this translation class"""

    _const_map = {
        # TS3 is not attached to a telescope so many translations are null.
        "telescope": "LSST",
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
        "detector_group": _DETECTOR_GROUP_NAME,
        "detector_name": _DETECTOR_NAME,  # Single sensor
        "detector_num": 0,
    }

    _trivial_map = {
        "detector_serial": "LSST_NUM",
        "physical_filter": "FILTER",
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
    }

    DETECTOR_GROUP_NAME = _DETECTOR_GROUP_NAME
    """Fixed name of detector group."""

    DETECTOR_NAME = _DETECTOR_NAME
    """Fixed name of single sensor."""

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
    def compute_detector_exposure_id(exposure_id, detector_num):
        """Compute the detector exposure ID from detector number and
        exposure ID.

        This is a helper method to allow code working outside the translator
        infrastructure to use the same algorithm.

        Parameters
        ----------
        exposure_id : `int`
            Unique exposure ID.
        detector_num : `int`
            Detector number.

        Returns
        -------
        detector_exposure_id : `int`
            The calculated ID.
        """
        if detector_num != 0:
            log.warning("Unexpected non-zero detector number for TS3")
        return exposure_id

    @staticmethod
    def compute_exposure_id(dateobs, seqnum=0):
        """Helper method to calculate the TS8 exposure_id.

        Parameters
        ----------
        dateobs : `str`
            Date of observation in FITS ISO format.
        seqnum : `int`, unused
            Sequence number. Ignored.

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
    def to_instrument(self):
        """Calculate the instrument name.

        Returns
        -------
        instrume : `str`
            Name of the test stand and manufacturer.
            For example: "TS3-E2V"
        """
        manu = self._header["CCD_MANU"]
        self._used_these_cards("CCD_MANU")
        return f"TS3-{manu}"

    @cache_translation
    def to_datetime_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        self._used_these_cards("MJD-OBS")
        return Time(self._header["MJD-OBS"], scale="utc", format="mjd")

    @cache_translation
    def to_datetime_end(self):
        # Docstring will be inherited. Property defined in properties.py
        return self.to_datetime_begin() + self.to_exposure_time()

    @cache_translation
    def to_dark_time(self):
        """Calculate the dark time.

        If a DARKTIME header is not found, the value is assumed to be
        identical to the exposure time.

        Returns
        -------
        dark : `astropy.units.Quantity`
            The dark time in seconds.
        """
        if "DARKTIME" in self._header:
            darktime = self._header("DARKTIME")*u.s
        else:
            log.warning("Unable to determine dark time. Setting from exposure time.")
            darktime = self.to_exposure_time()
        return darktime

    @cache_translation
    def to_detector_exposure_id(self):
        # Docstring will be inherited. Property defined in properties.py
        exposure_id = self.to_exposure_id()
        num = self.to_detector_num()
        return self.compute_detector_exposure_id(exposure_id, num)

    def to_exposure_id(self):
        """Generate a unique exposure ID number

        Note that SEQNUM is not unique for a given day in TS8 data
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
    def to_observation_type(self):
        # Docstring will be inherited. Property defined in properties.py
        obstype = self._header["IMGTYPE"]
        self._used_these_cards("IMGTYPE")
        return obstype.lower()
