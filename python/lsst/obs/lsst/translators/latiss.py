# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for LSST LATISS headers"""

__all__ = ("LsstLatissTranslator", )

import logging

import astropy.units as u
from astropy.time import Time
from astropy.coordinates import EarthLocation

from astro_metadata_translator import cache_translation
from astro_metadata_translator.translators.helpers import is_non_science
from .lsst import LsstBaseTranslator

log = logging.getLogger(__name__)


# AuxTel is not the same place as LSST
# These coordinates read from Apple Maps
AUXTEL_LOCATION = EarthLocation.from_geodetic(-70.747698, -30.244728, 2663.0)

# Date instrument is taking data at telescope
# Prior to this date many parameters are automatically nulled out
# since the headers have not historically been reliable
TSTART = Time("2019-12-08T00:00", format="isot", scale="utc")

# Define the sensor and group name for AuxTel globally so that it can be used
# in multiple places. There is no raft but for consistency with other LSST
# cameras we define one.
_DETECTOR_GROUP_NAME = "RXX"
_DETECTOR_NAME = "S00"


def is_non_science_or_lab(self):
    """Pseudo method to determine whether this is a lab or non-science
    header.

    Raises
    ------
    KeyError
        If this is a science observation and on the mountain.
    """
    # Return without raising if this is not a science observation
    # since the defaults are fine.
    try:
        # This will raise if it is a science observation
        is_non_science(self)
        return
    except KeyError:
        pass

    # We are still in the lab, return and use the default
    if not self._is_on_mountain():
        return

    # This is a science observation on the mountain so we should not
    # use defaults
    raise KeyError("Required key is missing and this is a mountain science observation")


class LsstLatissTranslator(LsstBaseTranslator):
    """Metadata translator for LSST LATISS data from AuxTel.

    For lab measurements many values are masked out.
    """

    name = "LSST_LATISS"
    """Name of this translation class"""

    supported_instrument = "LATISS"
    """Supports the LATISS instrument."""

    _const_map = {
        # LATISS is not yet attached to a telescope so many translations
        # are null.
        "instrument": "LATISS",
        "telescope": "LSSTAuxTel",
        "detector_group": _DETECTOR_GROUP_NAME,
        "detector_num": 0,
        "detector_name": _DETECTOR_NAME,  # Single sensor
        "boresight_rotation_coord": "unknown",
        "science_program": "unknown",
        "relative_humidity": None,
        "pressure": None,
        "temperature": None,
        "altaz_begin": None,
        "tracking_radec": None,
    }

    _trivial_map = {
        "observation_id": ("OBSID", dict(default=None, checker=is_non_science)),
        "detector_serial": ["LSST_NUM", "DETSER"],
        "boresight_airmass": ("AMSTART", dict(checker=is_non_science_or_lab)),
        "object": ("OBJECT", dict(checker=is_non_science_or_lab, default="UNKNOWN")),
        "boresight_rotation_angle": ("ROTANGLE", dict(checker=is_non_science_or_lab,
                                                      default=float("nan"), unit=u.deg)),
    }

    DETECTOR_GROUP_NAME = _DETECTOR_GROUP_NAME
    """Fixed name of detector group."""

    DETECTOR_NAME = _DETECTOR_NAME
    """Fixed name of single sensor."""

    DETECTOR_MAX = 0
    """Maximum number of detectors to use when calculating the
    detector_exposure_id."""

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
            instrume = header["INSTRUME"]
            for v in ("LSST_ATISS", "LATISS"):
                if instrume == v:
                    return True
        # Calibration files strip important headers at the moment so guess
        if "DETNAME" in header and header["DETNAME"] == "RXX_S00":
            return True
        return False

    def _is_on_mountain(self):
        date = self.to_datetime_begin()
        if date > TSTART:
            return True
        return False

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
            log.warning("Unexpected non-zero detector number for LATISS")
        return exposure_id

    @cache_translation
    def to_location(self):
        # Docstring will be inherited. Property defined in properties.py
        if self._is_on_mountain():
            return AUXTEL_LOCATION
        return None

    @cache_translation
    def to_dark_time(self):
        # Docstring will be inherited. Property defined in properties.py
        if self.is_key_ok("DARKTIME"):
            return self.quantity_from_card("DARKTIME", u.s)

        log.warning("Explicit dark time not found, setting dark time to the exposure time.")
        return self.to_exposure_time()

    @cache_translation
    def to_exposure_time(self):
        # Docstring will be inherited. Property defined in properties.py
        # Some data is missing a value for EXPTIME.
        # Have to be careful we do not have circular logic when trying to
        # guess
        if self.is_key_ok("EXPTIME"):
            return self.quantity_from_card("EXPTIME", u.s)

        # A missing or undefined EXPTIME is problematic. Set to -1
        # to indicate that none was found.
        log.warning("Insufficient information to derive exposure time. Setting to -1.0s")
        return -1.0 * u.s

    @cache_translation
    def to_observation_type(self):
        """Determine the observation type.

        In the absence of an ``IMGTYPE`` header, assumes lab data is always a
        dark if exposure time is non-zero, else bias.

        Returns
        -------
        obstype : `str`
            Observation type.
        """

        # LATISS observation type is documented to appear in OBSTYPE
        # but for historical reasons prefers IMGTYPE.  Some data puts
        # it in GROUPID (which is meant to be for something else).
        # Test the keys in order until we find one that contains a
        # defined value.
        obstype_keys = ["OBSTYPE", "IMGTYPE"]

        # For now, hope that GROUPID does not contain an obs type value
        # when on the mountain.
        if not self._is_on_mountain():
            obstype_keys.append("GROUPID")

        for k in obstype_keys:
            if self.is_key_ok(k):
                obstype = self._header[k]
                self._used_these_cards(k)
                return obstype.lower()

        # In the absence of any observation type information, return
        # unknown unless we think it might be a bias.
        exptime = self.to_exposure_time()
        if exptime == 0.0:
            obstype = "bias"
        else:
            obstype = "unknown"
        log.warning("Unable to determine observation type. Guessing '%s'", obstype)
        return obstype
