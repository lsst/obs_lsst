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

"""Metadata translation code for LSST simulations"""

__all__ = ("LsstSimTranslator", )

import logging
import re


from astropy.time import Time

from astro_metadata_translator import cache_translation, StubTranslator
from astro_metadata_translator.translators.helpers import tracking_from_degree_headers, \
    altaz_from_degree_headers

from .lsst import LSST_LOCATION

log = logging.getLogger(__name__)


class LsstSimTranslator(StubTranslator):
    """Shared routines for LSST Simulated Data.
    """

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
        tel = self.to_telescope()
        if tel is not None and tel == "LSST":
            location = LSST_LOCATION
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
