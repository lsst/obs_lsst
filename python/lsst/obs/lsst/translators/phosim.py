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

import astropy.units as u
import astropy.units.cds as cds

from astro_metadata_translator import cache_translation
from astro_metadata_translator.translators.helpers import tracking_from_degree_headers, \
    altaz_from_degree_headers

from .lsstsim import LsstSimTranslator

log = logging.getLogger(__name__)


class PhosimTranslator(LsstSimTranslator):
    """Metadata translator for LSST PhoSim data.
    """

    name = "PhoSim"
    """Name of this translation class"""

    _const_map = {
        "instrument": "PhoSim",
        "boresight_rotation_coord": "sky",
        "observation_type": "science",
        "object": "unknown",
        "relative_humidity": 40.0,
    }

    _trivial_map = {
        "detector_group": "RAFTNAME",
        "observation_id": "OBSID",
        "science_program": "RUNNUM",
        "exposure_id": "OBSID",
        "visit_id": "OBSID",
        "physical_filter": "FILTER",
        "dark_time": ("DARKTIME", dict(unit=u.s)),
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
        "temperature": ("TEMPERA", dict(unit=u.deg_C)),
        "pressure": ("PRESS", dict(unit=cds.mmHg)),
        "boresight_rotation_angle": (["ROTANGZ", "ROTANGLE"], dict(unit=u.deg)),
        "boresight_airmass": "AIRMASS",
        "detector_name": "SENSNAME",
        "detector_serial": "LSST_NUM",
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
        return cls.can_translate_with_options(header, {"CREATOR": "PHOSIM", "TESTTYPE": "PHOSIM"},
                                              filename=filename)

    @cache_translation
    def to_tracking_radec(self):
        # Docstring will be inherited. Property defined in properties.py
        radecsys = ("RADESYS",)
        radecpairs = (("RATEL", "DECTEL"), ("RA_DEG", "DEC_DEG"), ("BORE-RA", "BORE-DEC"))
        return tracking_from_degree_headers(self, radecsys, radecpairs)

    @cache_translation
    def to_altaz_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        # Fallback to the "derive from ra/dec" if keys are missing
        if "ZENITH" in self._header and "AZIMUTH" in self._header:
            return altaz_from_degree_headers(self, (("ZENITH", "AZIMUTH"),),
                                             self.to_datetime_begin(), is_zd=set(["ZENITH"]))
        else:
            return super().to_altaz_begin()
