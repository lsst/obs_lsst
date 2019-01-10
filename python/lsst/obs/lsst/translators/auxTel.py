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
    raise KeyError("Required key is missing and this is a mountaint science observation")


class LsstAuxTelTranslator(StubTranslator):
    """Metadata translator for LSST Aux Tel data.

    For lab measurements many values are masked out.
    """

    name = "LSSTAuxTel"
    """Name of this translation class"""

    supported_instrument = "LATISS"
    """Supports the LATISS instrument."""

    _const_map = {
        # TS8 is not attached to a telescope so many translations are null.
        "instrument": "LATISS",
        "telescope": "LSSTAuxTel",
        "detector_group": "RXX",  # Single sensor, define a dummy raft
        "detector_num": 0,
        "detector_name": "S00",  # Single sensor
        "boresight_rotation_coord": "unknown",
        "science_program": "unknown",
        "relative_humidity": None,
        "pressure": None,
        "temperature": None,
        "altaz_begin": None,
        "tracking_radec": None,
    }

    _trivial_map = {
        "observation_id": "OBSID",
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
        "dark_time": ("EXPTIME", dict(unit=u.s)),
        "detector_serial": "LSST_NUM",
        "boresight_airmass": ("AMSTART", dict(checker=is_non_science_or_lab)),
        "object": ("OBJECT", dict(checker=is_non_science_or_lab)),
        "boresight_rotation_angle": ("ROTANGLE", dict(checker=is_non_science_or_lab,
                                                      default=float("NaN"), unit=u.deg)),
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
        # INSTRUME keyword might be of two types
        if "INSTRUME" in header:
            instrume = header["INSTRUME"]
            for v in ("LSST_ATISS", "LATISS"):
                if instrume == v:
                    return True
        return False

    def _is_on_mountain(self):
        date = self.to_datetime_begin()
        if date > TSTART:
            return True
        return False

    @cache_translation
    def to_location(self):
        # Docstring will be inherited. Property defined in properties.py
        if self._is_on_mountain():
            return AUXTEL_LOCATION
        return None

    @cache_translation
    def to_datetime_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        return Time(self._header["MJD-OBS"], scale="utc", format="mjd")

    @cache_translation
    def to_datetime_end(self):
        # Docstring will be inherited. Property defined in properties.py
        return self.to_datetime_begin() + self.to_exposure_time()

    @cache_translation
    def to_detector_exposure_id(self):
        # Docstring will be inherited. Property defined in properties.py
        return self.to_exposure_id()

    def to_exposure_id(self):
        """Generate a unique exposure ID number

        This is a combination of DAYOBS and SEQNUM.

        Returns
        -------
        exposure_id : `int`
            Unique exposure number.
        """
        dayobs = self._header["DAYOBS"]
        seqnum = self._header["SEQNUM"]
        self._used_these_cards("DAYOBS", "SEQNUM")

        # Form the number as a string zero padding the sequence number
        idstr = f"{dayobs}{seqnum:06d}"
        return int(idstr)

    to_visit_id = to_exposure_id

    @cache_translation
    def to_observation_type(self):
        """Determine the observation type.

        Lab data is always a dark if exposure time is non-zero, else bias.

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
        if exptime > 0.0:
            return "dark"
        return "bias"

    @cache_translation
    def to_physical_filter(self):
        # Docstring will be inherited. Property defined in properties.py
        if self._is_on_mountain():
            filter = self._header["FILTER"]
            self._used_these_cards("FILTER")
            return filter
        return None
