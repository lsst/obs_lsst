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

"""Metadata translation code for ImSim headers"""

__all__ = ("ImSimTranslator", )

import astropy.units as u
from astropy.coordinates import AltAz
import logging
from astro_metadata_translator import cache_translation

from astro_metadata_translator.translators.helpers import tracking_from_degree_headers

from .lsstsim import LsstSimTranslator

log = logging.getLogger(__name__)


class ImSimTranslator(LsstSimTranslator):
    """Metadata translation class for ImSim headers"""

    name = "ImSim"
    """Name of this translation class"""

    _const_map = {
        "instrument": "ImSim",
        "boresight_rotation_coord": "sky",
        "object": "unknown",
        "pressure": None,
        "temperature": None,
        "relative_humidity": 40.0,
    }

    _trivial_map = {
        "detector_group": "RAFTNAME",
        "detector_name": "SENSNAME",
        "observation_id": "OBSID",
        "science_program": "RUNNUM",
        "exposure_id": "OBSID",
        "visit_id": "OBSID",
        "physical_filter": "FILTER",
        "dark_time": ("DARKTIME", dict(unit=u.s)),
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
        "detector_serial": "LSST_NUM",
        "boresight_rotation_angle": ("ROTANGLE", dict(unit=u.deg)),
    }

    @classmethod
    def can_translate(cls, header, filename=None):
        """Indicate whether this translation class can translate the
        supplied header.

        There is no ``INSTRUME`` header in ImSim data. Instead we use
        the ``TESTTYPE`` header.

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
        return cls.can_translate_with_options(header, {"TESTTYPE": "IMSIM"},
                                              filename=filename)

    @cache_translation
    def to_tracking_radec(self):
        # Docstring will be inherited. Property defined in properties.py
        radecsys = ("RADESYS",)
        radecpairs = (("RATEL", "DECTEL"),)
        return tracking_from_degree_headers(self, radecsys, radecpairs)

    @cache_translation
    def to_altaz_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        if self.to_observation_type() == "science":
            # Derive from RADec in absence of any other information
            radec = self.to_tracking_radec()
            if radec is not None:
                altaz = radec.transform_to(AltAz)
                return altaz
        return None

    @cache_translation
    def to_boresight_airmass(self):
        # Docstring will be inherited. Property defined in properties.py
        altaz = self.to_altaz_begin()
        if altaz is not None:
            return altaz.secz.to_value()
        return None
