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

__all__ = ("LatissTranslator", )

import logging
import math

import astropy.units as u
from astropy.time import Time
from astropy.coordinates import EarthLocation

from astro_metadata_translator import cache_translation
from astro_metadata_translator.translators.helpers import is_non_science
from .lsst import LsstBaseTranslator, FILTER_DELIMITER

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

# OBJECT IMGTYPE really means ENGTEST until this date
OBJECT_IS_ENGTEST = Time("2020-01-27T20:00", format="isot", scale="utc")

# RA and DEC headers are in radians until this date
RADEC_IS_RADIANS = Time("2020-01-28T22:00", format="isot", scale="utc")

# RASTART/DECSTART/RAEND/DECEND used wrong telescope location before this
# 2020-02-01T00:00 we fixed the telescope location, but RASTART is still
# in mount coordinates, so off by pointing model.
RASTART_IS_BAD = Time("2020-05-01T00:00", format="isot", scale="utc")

# DATE-END is not to be trusted before this date
DATE_END_IS_BAD = Time("2020-02-01T00:00", format="isot", scale="utc")

# Scaling factor radians to degrees.  Keep it simple.
RAD2DEG = 180.0 / math.pi


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
    raise KeyError(f"{self._log_prefix}: Required key is missing and this is a mountain science observation")


class LatissTranslator(LsstBaseTranslator):
    """Metadata translator for LSST LATISS data from AuxTel.

    For lab measurements many values are masked out.
    """

    name = "LSST_LATISS"
    """Name of this translation class"""

    supported_instrument = "LATISS"
    """Supports the LATISS instrument."""

    _const_map = {
        "instrument": "LATISS",
        "telescope": "Rubin Auxiliary Telescope",
        "detector_group": _DETECTOR_GROUP_NAME,
        "detector_num": 0,
        "detector_name": _DETECTOR_NAME,  # Single sensor
        "science_program": "unknown",
        "relative_humidity": None,
        "pressure": None,
        "temperature": None,
    }

    _trivial_map = {
        "observation_id": (["OBSID", "IMGNAME"], dict(default=None, checker=is_non_science)),
        "detector_serial": ["LSST_NUM", "DETSER"],
        "object": ("OBJECT", dict(checker=is_non_science_or_lab, default="UNKNOWN")),
        "boresight_rotation_angle": (["ROTPA", "ROTANGLE"], dict(checker=is_non_science_or_lab,
                                                                 default=float("nan"), unit=u.deg)),
    }

    DETECTOR_GROUP_NAME = _DETECTOR_GROUP_NAME
    """Fixed name of detector group."""

    DETECTOR_NAME = _DETECTOR_NAME
    """Fixed name of single sensor."""

    DETECTOR_MAX = 0
    """Maximum number of detectors to use when calculating the
    detector_exposure_id."""

    _DEFAULT_LOCATION = AUXTEL_LOCATION
    """Default telescope location in absence of relevant FITS headers."""

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
    def fix_header(cls, header, instrument, obsid, filename=None):
        """Fix an incorrect LATISS header.

        Parameters
        ----------
        header : `dict`
            The header to update.  Updates are in place.
        instrument : `str`
            The name of the instrument.
        obsid : `str`
            Unique observation identifier associated with this header.
            Will always be provided.
        filename : `str`, optional
            Filename associated with this header. May not be set since headers
            can be fixed independently of any filename being known.

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

        See `~astro_metadata_translator.fix_header` for details of the general
        process.
        """
        modified = False

        # Calculate the standard label to use for log messages
        log_label = cls._construct_log_prefix(obsid, filename)

        if "OBSID" not in header:
            # Very old data used IMGNAME
            header["OBSID"] = obsid
            modified = True
            # We are reporting the OBSID so no need to repeat it at start
            # of log message. Use filename if we have it.
            log_prefix = f"{filename}: " if filename else ""
            log.debug("%sAssigning OBSID to a value of '%s'", log_prefix, header["OBSID"])

        if "DAYOBS" not in header:
            # OBS-NITE could have the value for DAYOBS but it is safer
            # for older data to set it from the OBSID. Fall back to OBS-NITE
            # if we have no alternative
            dayObs = None
            try:
                dayObs = obsid.split("_", 3)[2]
            except (AttributeError, ValueError):
                # did not split as expected
                pass
            if dayObs is None or len(dayObs) != 8:
                dayObs = header["OBS-NITE"]
                log.debug("%s: Setting DAYOBS to '%s' from OBS-NITE header", log_label, dayObs)
            else:
                log.debug("%s: Setting DAYOBS to '%s' from OBSID", log_label, dayObs)
            header["DAYOBS"] = dayObs
            modified = True

        if "SEQNUM" not in header:
            try:
                seqnum = obsid.split("_", 3)[3]
            except (AttributeError, ValueError):
                # did not split as expected
                pass
            else:
                header["SEQNUM"] = int(seqnum)
                modified = True
                log.debug("%s: Extracting SEQNUM of '%s' from OBSID", log_label, header["SEQNUM"])

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

            log.debug("%s: Forcing 1970 dates to '%s'", log_label, header["DATE"])
            modified = True

        # Create a translator since we need the date
        translator = cls(header)
        date = translator.to_datetime_begin()
        if date > DETECTOR_068_DATE:
            header["LSST_NUM"] = "ITL-3800C-068"
            log.debug("%s: Forcing detector serial to %s", log_label, header["LSST_NUM"])
            modified = True

        if date < DATE_END_IS_BAD:
            # DATE-END may or may not be in TAI and may or may not be
            # before DATE-BEG.  Simpler to clear it
            if header.get("DATE-END"):
                header["DATE-END"] = None
                header["MJD-END"] = None

                log.debug("%s: Clearing DATE-END as being untrustworthy", log_label)
                modified = True

        # Up until a certain date GROUPID was the IMGTYPE
        if date < IMGTYPE_OKAY_DATE:
            groupId = header.get("GROUPID")
            if groupId and not groupId.startswith("test"):
                imgType = header.get("IMGTYPE")
                if not imgType:
                    if "_" in groupId:
                        # Sometimes have the form dark_0001_0002
                        # in this case we pull the IMGTYPE off the front and
                        # do not clear groupId (although groupId may now
                        # repeat on different days).
                        groupId, _ = groupId.split("_", 1)
                    elif groupId.upper() != "FOCUS" and groupId.upper().startswith("FOCUS"):
                        # If it is exactly FOCUS we want groupId cleared
                        groupId = "FOCUS"
                    else:
                        header["GROUPID"] = None
                    header["IMGTYPE"] = groupId
                    log.debug("%s: Setting IMGTYPE to '%s' from GROUPID", log_label, header["IMGTYPE"])
                    modified = True
                else:
                    # Someone could be fixing headers in old data
                    # and we do not want GROUPID == IMGTYPE
                    if imgType == groupId:
                        # Clear the group so we default to original
                        header["GROUPID"] = None

        # We were using OBJECT for engineering observations early on
        if date < OBJECT_IS_ENGTEST:
            imgType = header.get("IMGTYPE")
            if imgType == "OBJECT":
                header["IMGTYPE"] = "ENGTEST"
                log.debug("%s: Changing OBJECT observation type to %s",
                          log_label, header["IMGTYPE"])
                modified = True

        # Early on the RA/DEC headers were stored in radians
        if date < RADEC_IS_RADIANS:
            if header.get("RA") is not None:
                header["RA"] *= RAD2DEG
                log.debug("%s: Changing RA header to degrees", log_label)
                modified = True
            if header.get("DEC") is not None:
                header["DEC"] *= RAD2DEG
                log.debug("%s: Changing DEC header to degrees", log_label)
                modified = True

        if header.get("SHUTTIME"):
            log.debug("%s: Forcing SHUTTIME header to be None", log_label)
            header["SHUTTIME"] = None
            modified = True

        if "OBJECT" not in header:
            # Only patch OBJECT IMGTYPE
            if "IMGTYPE" in header and header["IMGTYPE"] == "OBJECT":
                log.debug("%s: Forcing OBJECT header to exist", log_label)
                header["OBJECT"] = "NOTSET"
                modified = True

        if "RADESYS" in header:
            if header["RADESYS"] == "":
                # Default to ICRS
                header["RADESYS"] = "ICRS"
                log.debug("%s: Forcing blank RADESYS to '%s'", log_label, header["RADESYS"])
                modified = True

        if date < RASTART_IS_BAD:
            # The wrong telescope position was used. Unsetting these will force
            # the RA/DEC demand headers to be used instead.
            for h in ("RASTART", "DECSTART", "RAEND", "DECEND"):
                header[h] = None
            log.debug("%s: Forcing derived RA/Dec headers to undefined", log_label)

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
                    self._log_prefix, reason)
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
                    self._log_prefix)
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
                    self._log_prefix, obstype)
        return obstype

    @cache_translation
    def to_physical_filter(self):
        """Calculate the physical filter name.

        Returns
        -------
        filter : `str`
            Name of filter. A combination of FILTER and GRATING
            headers joined by a "~".  The filter and grating are always
            combined.  The filter or grating part will be "NONE" if no value
            is specified.  Uses "EMPTY" if any of the filters or gratings
            indicate an "empty_N" name. "UNKNOWN" indicates that the filter is
            not defined anywhere but we think it should be.  "NONE" indicates
            that the filter was not defined but the observation is a dark
            or bias.
        """

        physical_filter = self._determine_primary_filter()

        if self.is_key_ok("GRATING"):
            grating = self._header["GRATING"]
            self._used_these_cards("GRATING")

            if not grating or grating.lower().startswith("empty"):
                grating = "EMPTY"
        else:
            # Be explicit about having no knowledge of the grating
            grating = "UNKNOWN"

        physical_filter = f"{physical_filter}{FILTER_DELIMITER}{grating}"

        return physical_filter

    @cache_translation
    def to_boresight_rotation_coord(self):
        """Boresight rotation angle.

        Only relevant for science observations.
        """
        unknown = "unknown"
        if not self.is_on_sky():
            return unknown

        self._used_these_cards("ROTCOORD")
        coord = self._header.get("ROTCOORD", unknown)
        if coord is None:
            coord = unknown
        return coord

    @cache_translation
    def to_boresight_airmass(self):
        """Calculate airmass at boresight at start of observation.

        Notes
        -----
        Early data are missing AMSTART header so we fall back to calculating
        it from ELSTART.
        """
        if not self.is_on_sky():
            return None

        # This observation should have AMSTART
        amkey = "AMSTART"
        if self.is_key_ok(amkey):
            self._used_these_cards(amkey)
            return self._header[amkey]

        # Instead we need to look at azel
        altaz = self.to_altaz_begin()
        if altaz is not None:
            return altaz.secz.to_value()

        log.warning("%s: Unable to determine airmass of a science observation, returning 1.",
                    self._log_prefix)
        return 1.0
