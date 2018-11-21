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

"""Metadata translation code for LSST PhoSim FITS headers"""

__all__ = ("PhosimTranslator", )

import logging
import re

from astropy.coordinates import EarthLocation
import astropy.units as u
import astropy.units.cds as cds
from astropy.time import Time
# from astropy.coordinates import Angle

from astro_metadata_translator import cache_translation, StubTranslator
from astro_metadata_translator.translators.helpers import tracking_from_degree_headers, \
    altaz_from_degree_headers

log = logging.getLogger(__name__)


class PhosimTranslator(StubTranslator):
    """Metadata translator for LSST PhoSim data.
    """

    name = "PhoSim"
    """Name of this translation class"""

    _const_map = {
        "instrument": "PhoSim",
        "boresight_rotation_coord": "sky",
        "observation_type": "science",
        "object": "unknown",
        "science_program": "phosim",
        "relative_humidity": 40.0,
    }

    _trivial_map = {
        "observation_id": "OBSID",
        "exposure_id": "OBSID",
        "visit_id": "OBSID",
        "physical_filter": "FILTER",
        "dark_time": ("DARKTIME", dict(unit=u.s)),
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
        "temperature": ("TEMPERA", dict(unit=u.deg_C)),
        "pressure": ("PRESS", dict(unit=cds.mmHg)),
        "boresight_rotation_angle": ("ROTANGZ", dict(unit=u.deg)),
        "boresight_airmass": "AIRMASS",
        "detector_name": "CCDID",
    }

    @classmethod
    def can_translate(cls, header, filename=None):
        """Indicate whether this translation class can translate the
        supplied header.

        There is no ``INSTRUME`` header in PhoSim data. Instead we use
        the ``CREATOR`` header.

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
        if "CREATOR" in header:
            return header["CREATOR"] == "PHOSIM"
        return False

    @cache_translation
    def to_telescope(self):
        # Docstring will be inherited. Property defined in properties.py
        telescope = None
        if self._header["OUTFILE"].startswith("lsst"):
            telescope = "LSST"
        self._used_these_cards("OUTFILE")
        return telescope

    @cache_translation
    def to_location(self):
        # Docstring will be inherited. Property defined in properties.py
        location = None
        if self._header["OUTFILE"].startswith("lsst"):
            location = EarthLocation.from_geodetic(-30.244639, -70.749417, 2663.0)
        self._used_these_cards("OUTFILE")
        return location

    @cache_translation
    def to_datetime_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        return Time(self._header["MJD-OBS"], scale="tai", format="mjd")

    @cache_translation
    def to_datetime_end(self):
        # Docstring will be inherited. Property defined in properties.py
        return self.to_datetime_begin() + self.to_exposure_time()

    @cache_translation
    def to_tracking_radec(self):
        # Docstring will be inherited. Property defined in properties.py
        radecsys = ("RADESYS",)
        radecpairs = (("RA_DEG", "DEC_DEG"), ("BORE-RA", "BORE-DEC"))
        return tracking_from_degree_headers(self, radecsys, radecpairs)

    @cache_translation
    def to_altaz_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        return altaz_from_degree_headers(self, (("ZENITH", "AZIMUTH"),),
                                         self.to_datetime_begin(), is_zd=set(["ZENITH"]))

    @cache_translation
    def to_detector_num(self):
        # Docstring will be inherited. Property defined in properties.py
        name = self.to_detector_name()
        match = re.match(r"R(\d\d)_S(\d)(\d)$", name)
        if not match:
            raise ValueError(f"Detector number has unexpected form 'f{name}'")
        r, ccdx, ccdy = match.groups()
        num = int(r)*9 + int(ccdy)*3 + int(ccdx)
        return num

    @cache_translation
    def to_detector_exposure_id(self):
        exposure_id = self.to_exposure_id()
        num = self.to_detector_num()
        return 200*exposure_id + num
