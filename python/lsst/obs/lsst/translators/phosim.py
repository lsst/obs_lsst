# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for LSSTCam PhoSim FITS headers"""

__all__ = ("LsstCamPhoSimTranslator",)

import logging

import astropy.io.fits as fits
import astropy.units as u
import astropy.units.cds as cds
from astropy.coordinates import Angle
from astropy.time import TimeDelta

from astro_metadata_translator import cache_translation, merge_headers
from astro_metadata_translator.translators.helpers import (
    tracking_from_degree_headers,
    altaz_from_degree_headers,
)

from lsst.resources import ResourcePath

from .lsstsim import LsstSimTranslator

log = logging.getLogger(__name__)


class LsstCamPhoSimTranslator(LsstSimTranslator):
    """Metadata translator for LSSTCam PhoSim data."""

    name = "LSSTCam-PhoSim"
    """Name of this translation class"""

    _const_map = {
        "instrument": "LSSTCam-PhoSim",
        "boresight_rotation_coord": "sky",
        "observation_type": "science",
        "object": "UNKNOWN",
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
        "boresight_airmass": "AIRMASS",
        "detector_name": "SENSNAME",
        "detector_serial": "LSST_NUM",
    }

    cameraPolicyFile = "policy/phosim.yaml"

    _ROLLOVER_TIME = TimeDelta(0, scale="tai", format="sec")
    """This instrument did not offset the observing day."""

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
        # Generic PhoSim data does not have an INSTRUME header.
        # If an INSTRUME header is present this translator class
        # is not suitable.
        if "INSTRUME" in header:
            return False
        else:
            return cls.can_translate_with_options(
                header, {"CREATOR": "PHOSIM", "TESTTYPE": "PHOSIM"}, filename=filename
            )

    @cache_translation
    def to_tracking_radec(self):
        # Docstring will be inherited. Property defined in properties.py
        radecsys = ("RADESYS",)
        radecpairs = (
            ("RATEL", "DECTEL"),
            ("RA_DEG", "DEC_DEG"),
            ("BORE-RA", "BORE-DEC"),
        )
        return tracking_from_degree_headers(self, radecsys, radecpairs)

    @cache_translation
    def to_altaz_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        # Fallback to the "derive from ra/dec" if keys are missing
        if self.are_keys_ok(["ZENITH", "AZIMUTH"]):
            return altaz_from_degree_headers(
                self,
                (("ZENITH", "AZIMUTH"),),
                self.to_datetime_begin(),
                is_zd=set(["ZENITH"]),
            )
        else:
            return super().to_altaz_begin()

    @cache_translation
    def to_boresight_rotation_angle(self):
        angle = Angle(90.0 * u.deg) - Angle(
            self.quantity_from_card(["ROTANGZ", "ROTANGLE"], u.deg)
        )
        angle = angle.wrap_at("360d")
        return angle

    @classmethod
    def determine_translatable_headers(cls, filename, primary=None):
        """Given a file return all the headers usable for metadata translation.

        Phosim splits useful metadata between the primary header and the
        amplifier headers. A single header is returned as a merge of the
        first two.

        Parameters
        ----------
        filename : `str` or `lsst.resources.ResourcePathExpression`
            Path to a file in a format understood by this translator.
        primary : `dict`-like, optional
            The primary header obtained by the caller. This is sometimes
            already known, for example if a system is trying to bootstrap
            without already knowing what data is in the file. Will be
            ignored.

        Yields
        ------
        headers : iterator of `dict`-like
            The primary header merged with the secondary header.

        Notes
        -----
        This translator class is specifically tailored to raw PhoSim data
        and is not designed to work with general FITS files. The normal
        paradigm is for the caller to have read the first header and then
        called `determine_translator()` on the result to work out which
        translator class to then call to obtain the real headers to be used for
        translation.
        """
        uri = ResourcePath(filename, forceDirectory=False)
        fs, fspath = uri.to_fsspec()
        with fs.open(fspath) as f, fits.open(f) as fits_file:
            yield merge_headers([fits_file[0].header, fits_file[1].header],
                                mode="overwrite")
