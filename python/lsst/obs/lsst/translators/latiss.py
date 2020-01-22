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
import re

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
TSTART = Time("2020-01-01T00:00", format="isot", scale="utc")

# Define the sensor and group name for AuxTel globally so that it can be used
# in multiple places. There is no raft but for consistency with other LSST
# cameras we define one.
_DETECTOR_GROUP_NAME = "RXX"
_DETECTOR_NAME = "S00"

# Date 068 detector was put in LATISS
DETECTOR_068_DATE = Time("2019-06-24T00:00", format="isot", scale="utc")

# IMGTYPE header is filled in after this date
IMGTYPE_OKAY_DATE = Time("2019-11-07T00:00", format="isot", scale="utc")


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

    @classmethod
    def fix_header(cls, header):
        """Fix an incorrect LATISS header.

        Parameters
        ----------
        header : `dict`
            The header to update.  Updates are in place.

        Returns
        -------
        modified = `bool`
            Returns `True` if the header was updated.

        Notes
        -----
        This method does not apply per-obsid corrections.  The following
        corrections are applied:

        * On June 24th 2019 the detector was changed from ITL-3800C-098
          to ITL-3800C-068.  The header is intended to be correct in the
          future.
        * In late 2019 the DATE-OBS and MJD-OBS headers were reporting
          1970 dates.  To correct, the DATE/MJD headers are copied in to
          replace them and the -END headers are cleared.
        * Until November 2019 the IMGTYPE was set in the GROUPID header.
          The value is moved to IMGTYPE.
        * SHUTTIME is always forced to be `None`.

        Corrections are reported as debug level log messages.
        """
        modified = False

        obsid = header.get("OBSID", "unknown")

        # The DATE-OBS / MJD-OBS keys can be 1970
        if header["DATE-OBS"].startswith("1970"):
            # Copy the headers from the DATE and MJD since we have no other
            # choice.
            header["DATE-OBS"] = header["DATE"]
            header["DATE-BEG"] = header["DATE-OBS"]
            header["MJD-OBS"] = header["MJD"]
            header["MJD-BEG"] = header["MJD-OBS"]

            # And clear the DATE-END and MJD-END -- the translator will use
            # EXPTIME instead.
            header["DATE-END"] = None
            header["MJD-END"] = None

            log.debug("%s: Forcing 1970 dates to '%s'", obsid, header["DATE"])
            modified = True

        # Create a translator since we need the date
        translator = cls(header)
        date = translator.to_datetime_begin()
        if date > DETECTOR_068_DATE:
            header["LSST_NUM"] = "ITL-3800C-068"
            log.debug("%s: Forcing detector serial to %s", obsid, header["LSST_NUM"])
            modified = True

        # Up until a certain date GROUPID was the IMGTYPE
        if date < IMGTYPE_OKAY_DATE:
            groupId = header.get("GROUPID")
            if groupId and not groupId.startswith("test"):
                imgType = header.get("IMGTYPE")
                if not imgType:
                    header["IMGTYPE"] = groupId
                    header["GROUPID"] = None
                    log.debug("%s: Setting IMGTYPE from GROUPID", obsid)
                    modified = True

        if header.get("SHUTTIME"):
            log.debug("%s: Forcing SHUTTIME header to be None", obsid)
            header["SHUTTIME"] = None
            modified = True

        if "OBJECT" not in header:
            # Only patch OBJECT IMGTYPE
            if "IMGTYPE" in header and header["IMGTYPE"] == "OBJECT":
                log.debug("%s: Forcing OBJECT header to exist", obsid)
                header["OBJECT"] = "NOTSET"
                modified = True

        return modified

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

        # Always compare with exposure time
        # We may revisit this later if there is a cutoff date where we
        # can always trust the header.
        exptime = self.to_exposure_time()

        if self.is_key_ok("DARKTIME"):
            darktime = self.quantity_from_card("DARKTIME", u.s)
            if darktime >= exptime:
                return darktime
            reason = "Dark time less than exposure time."
        else:
            reason = "Dark time not defined."

        log.warning("%s: %s Setting dark time to the exposure time.",
                    self.to_observation_id(), reason)
        return exptime

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
        log.warning("%s: Insufficient information to derive exposure time. Setting to -1.0s",
                    self.to_observation_id())
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
        # but for historical reasons prefers IMGTYPE.
        # Test the keys in order until we find one that contains a
        # defined value.
        obstype_keys = ["OBSTYPE", "IMGTYPE"]

        obstype = None
        for k in obstype_keys:
            if self.is_key_ok(k):
                obstype = self._header[k]
                self._used_these_cards(k)
                obstype = obstype.lower()
                break

        if obstype is not None:
            if obstype == "object" and not self._is_on_mountain():
                # Do not map object to science in lab since most
                # code assume science is on sky with RA/Dec.
                obstype = "labobject"
            elif obstype in ("skyexp", "object"):
                obstype = "science"

            return obstype

        # In the absence of any observation type information, return
        # unknown unless we think it might be a bias.
        exptime = self.to_exposure_time()
        if exptime == 0.0:
            obstype = "bias"
        else:
            obstype = "unknown"
        log.warning("%s: Unable to determine observation type. Guessing '%s'",
                    self.to_observation_id(), obstype)
        return obstype

    @cache_translation
    def to_physical_filter(self):
        """Calculate the physical filter name.

        Returns
        -------
        filter : `str`
            Name of filter. Can be a combination of FILTER, FILTER1 and FILTER2
            headers joined by a "+".  Returns "NONE" if no filter is declared.
            Uses "EMPTY" if any of the filters indicate an "empty_N" name.
        """
        # The base class definition is fine
        physical_filter = super().to_physical_filter()

        # empty_N maps to EMPTY at the start of a filter concatenation
        if physical_filter.startswith("empty"):
            physical_filter = re.sub(r"^empty_\d+", "EMPTY", physical_filter)

        return physical_filter
