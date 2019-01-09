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

from astropy.time import Time

from astro_metadata_translator import cache_translation, StubTranslator

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
    def to_detector_num(self):
        # Docstring will be inherited. Property defined in properties.py
        raft = self.to_detector_group()
        detector = self.to_detector_name()

        try:
            rnum = int(raft[1:])
        except Exception as e:
            raise ValueError(f"Raft name in unexpected format ({raft})") from e

        try:
            ccdx = int(detector[1])
            ccdy = int(detector[2])
        except Exception as e:
            raise ValueError(f"Unexpected form for detector name ({detector})") from e
        num = rnum*9 + ccdy*3 + ccdx
        return num

    @cache_translation
    def to_detector_exposure_id(self):
        exposure_id = self.to_exposure_id()
        num = self.to_detector_num()
        return 200*exposure_id + num

    @cache_translation
    def to_observation_type(self):
        # Docstring will be inherited. Property defined in properties.py
        obstype = self._header["IMGTYPE"]
        self._used_these_cards("IMGTYPE")
        obstype = obstype.lower()
        if obstype == "skyexp":
            obstype = "science"
        return obstype
