# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for LSSTCam imSim headers"""

__all__ = ("LsstCamImSimTranslator", )

import logging
import astropy.units as u
from astropy.coordinates import Angle, AltAz

try:
    import erfa
except ImportError:
    import astropy._erfa as erfa

from astro_metadata_translator import cache_translation
from astro_metadata_translator.translators.helpers import tracking_from_degree_headers

from .lsstsim import LsstSimTranslator

log = logging.getLogger(__name__)


class LsstCamImSimTranslator(LsstSimTranslator):
    """Metadata translation class for LSSTCam imSim headers"""

    name = "LSSTCam-imSim"
    """Name of this translation class"""

    _const_map = {
        "instrument": "LSSTCam-imSim",
        "boresight_rotation_coord": "sky",
        "object": "UNKNOWN",
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
        "dark_time": ("DARKTIME", dict(unit=u.s)),
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
        "detector_serial": "LSST_NUM",
    }

    cameraPolicyFile = "policy/imsim.yaml"

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
    def to_boresight_airmass(self):
        # Docstring will be inherited. Property defined in properties.py
        for key in ("AIRMASS", "AMSTART"):
            if self.is_key_ok(key):
                return self._header[key]
        altaz = self.to_altaz_begin()
        if altaz is not None:
            return altaz.secz.to_value()
        return None

    @cache_translation
    def to_boresight_rotation_angle(self):
        angle = Angle(90.*u.deg) - Angle(self.quantity_from_card("ROTANGLE", u.deg))
        angle = angle.wrap_at("360d")
        return angle

    @cache_translation
    def to_physical_filter(self):
        # Find throughputs version from imSim header data.  For DC2
        # data, we used throughputs version 1.4.
        throughputs_version = None
        for key, value in self._header.items():
            if key.startswith("PKG") and value == "throughputs":
                version_key = "VER" + key[len("PKG"):]
                throughputs_version = self._header[version_key].strip()
                break
        if throughputs_version is None:
            log.warning("%s: throughputs version not found.  Using FILTER keyword value '%s'.",
                        self.to_observation_id(), self._header["FILTER"])
            return self._header["FILTER"]
        return "_".join((self._header["FILTER"], "sim", throughputs_version))

    @cache_translation
    def to_altaz_begin(self):
        # Calculate from the hour angle if available
        if self.to_observation_type() != "science":
            return None

        if not self.are_keys_ok(["HASTART", "DECTEL"]):
            # Fallback to slow method
            return super().to_altaz_begin()

        location = self.to_location()
        ha = Angle(self._header["HASTART"], unit=u.deg)

        # For speed over accuracy, assume this is apparent Dec not ICRS
        dec = Angle(self._header["DECTEL"], unit=u.deg)

        # Use erfa directly
        az, el = erfa.hd2ae(ha.radian, dec.radian, location.lat.radian)

        return AltAz(az*u.radian, el*u.radian,
                     obstime=self.to_datetime_begin(), location=location)
