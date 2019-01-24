# This file is part of obs_lsst.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Metadata translation code for LSST TestStand 8 headers"""

__all__ = ("LsstAuxTelTranslator", )

import logging

import astropy.units as u
from astropy.time import Time
from astropy.coordinates import EarthLocation

from astro_metadata_translator import cache_translation, StubTranslator
from astro_metadata_translator.translators.helpers import is_non_science

log = logging.getLogger(__name__)


# AuxTel is not the same place as LSST
# These coordinates read from Apple Maps
AUXTEL_LOCATION = EarthLocation.from_geodetic(-30.244728, -70.747698, 2663.0)

# Date instrument is taking data at telescope
# Prior to this date many parameters are automatically nulled out
# since the headers have not historically been reliable
TSTART = Time("2019-06-01T00:00", format="isot", scale="utc")

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
    if is_non_science(self):
        return
    if not self._is_on_mountain():
        return
    raise KeyError("Required key is missing and this is a mountain science observation")


class LsstAuxTelTranslator(StubTranslator):
    """Metadata translator for LSST AuxTel data.

    For lab measurements many values are masked out.
    """

    name = "LSSTAuxTel"
    """Name of this translation class"""

    supported_instrument = "LATISS"
    """Supports the LATISS instrument."""

    _const_map = {
        # AuxTel is not yet attached to a telescope so many translations are null.
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
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
        "dark_time": (["DARKTIME", "EXPTIME"], dict(unit=u.s)),
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
            log.warning("Unexpected non-zero detector number for AuxTel")
        return exposure_id

    @staticmethod
    def compute_exposure_id(dayobs, seqnum):
        """Helper method to calculate the AuxTel exposure_id.

        Parameters
        ----------
        dayobs : `str`
            Day of observation in either YYYYMMDD or YYYY-MM-DD format.
        seqnum : `int` or `str`
            Sequence number.

        Returns
        -------
        exposure_id : `int`
            Exposure ID in form YYYYMMDDnnnnn form.
        """
        dayobs = dayobs.replace("-", "")

        # Form the number as a string zero padding the sequence number
        idstr = f"{dayobs}{seqnum:06d}"
        return int(idstr)

    @cache_translation
    def to_location(self):
        # Docstring will be inherited. Property defined in properties.py
        if self._is_on_mountain():
            return AUXTEL_LOCATION
        return None

    @cache_translation
    def to_datetime_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        if "MJD-OBS" in self._header:
            self._used_these_cards("MJD-OBS")
            return Time(self._header["MJD-OBS"], scale="utc", format="mjd")
        if "CALIB_ID" in self._header:
            # Calibration files hide the date information
            calib_id = self._header["CALIB_ID"]
            self._used_these_cards("CALIB_ID")
            parts = calib_id.split()
            for p in parts:
                if p.startswith("calibDate"):
                    ymd = p[10:]
                    return Time(ymd, scale="utc", format="isot")
        return None

    @cache_translation
    def to_datetime_end(self):
        # Docstring will be inherited. Property defined in properties.py
        return self.to_datetime_begin() + self.to_exposure_time()

    @cache_translation
    def to_detector_exposure_id(self):
        # Docstring will be inherited. Property defined in properties.py
        exposure_id = self.to_exposure_id()
        detector_num = self.to_detector_num()
        return self.compute_detector_exposure_id(exposure_id, detector_num)

    @cache_translation
    def to_exposure_id(self):
        """Generate a unique exposure ID number

        This is a combination of DAYOBS and SEQNUM.

        Returns
        -------
        exposure_id : `int`
            Unique exposure number.
        """
        if "CALIB_ID" in self._header:
            self._used_these_cards("CALIB_ID")
            return None

        dayobs = self._header["DAYOBS"]
        seqnum = self._header["SEQNUM"]
        self._used_these_cards("DAYOBS", "SEQNUM")

        return self.compute_exposure_id(dayobs, seqnum)

    # For now "visits" are defined to be identical to exposures.
    to_visit_id = to_exposure_id

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
        if self._is_on_mountain():
            obstype = self._header["IMGTYPE"]
            self._used_these_cards("IMGTYPE")
            return obstype.lower()

        exptime = self.to_exposure_time()
        if exptime == 0.0:
            obstype = "bias"
        else:
            obstype = "unknown"
        log.warning("Unable to determine observation type. Guessing '%s'", obstype)
        return obstype

    @cache_translation
    def to_physical_filter(self):
        # Docstring will be inherited. Property defined in properties.py
        filters = []
        for k in ("FILTER1", "FILTER2"):
            if k in self._header:
                filters.append(self._header[k])
                self._used_these_cards(k)

        if filters:
            filterName = "|".join(filters)
        else:
            filterName = "NONE"

        return filterName
