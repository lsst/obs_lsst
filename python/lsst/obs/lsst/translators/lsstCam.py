# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for the main LSST Camera"""

__all__ = ("LsstCamTranslator", )

import logging

import pytz
import astropy.time
import astropy.units as u
from astropy.time import Time

from astro_metadata_translator import cache_translation
from astro_metadata_translator.translators.helpers import is_non_science

from .lsst import LsstBaseTranslator, SIMONYI_TELESCOPE

log = logging.getLogger(__name__)

# Normalized name of the LSST Camera
LSST_CAM = "LSSTCam"


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
        # This will raise if it is a science observation.
        is_non_science(self)
        return
    except KeyError:
        pass

    # We are still in the lab, return and use the default.
    if not self._is_on_mountain():
        return

    # This is a science observation on the mountain so we should not
    # use defaults.
    raise KeyError(f"{self._log_prefix}: Required key is missing and this is a mountain science observation")


class LsstCamTranslator(LsstBaseTranslator):
    """Metadata translation for the main LSST Camera."""

    name = LSST_CAM
    """Name of this translation class"""

    supported_instrument = LSST_CAM
    """Supports the lsstCam instrument."""

    _const_map = {
        "instrument": LSST_CAM,
        "telescope": SIMONYI_TELESCOPE,
    }

    _trivial_map = {
        "detector_group": "RAFTBAY",
        "detector_name": "CCDSLOT",
        "observation_id": "OBSID",
        "detector_serial": "LSST_NUM",
        "object": ("OBJECT", dict(default="UNKNOWN")),
        "science_program": (["PROGRAM", "RUNNUM"], dict(default="unknown")),
        "boresight_rotation_angle": (["ROTPA", "ROTANGLE"], dict(checker=is_non_science_or_lab,
                                                                 default=0.0, unit=u.deg)),
    }

    # Use Imsim raft definitions until a true lsstCam definition exists
    cameraPolicyFile = "policy/lsstCam.yaml"

    # Date (YYYYMM) the camera changes from using lab day_offset (Pacific time)
    # to summit day_offset (12 hours).
    _CAMERA_SHIP_DATE = 202405

    @classmethod
    def fix_header(cls, header, instrument, obsid, filename=None):
        """Fix LSSTCam headers.

        Notes
        -----
        See `~astro_metadata_translator.fix_header` for details of the general
        process.
        """

        modified = False

        # Calculate the standard label to use for log messages
        log_label = cls._construct_log_prefix(obsid, filename)

        if "FILTER" not in header and header.get("FILTER2") is not None:
            ccdslot = header.get("CCDSLOT", "unknown")
            raftbay = header.get("RAFTBAY", "unknown")

            log.warning("%s %s_%s: No FILTER key found but FILTER2=\"%s\" (removed)",
                        log_label, raftbay, ccdslot, header["FILTER2"])
            header["FILTER2"] = None
            modified = True

        if header.get("DAYOBS") in ("20231107", "20231108") and header["FILTER"] == "ph_05":
            header["FILTER"] = "ph_5"
            modified = True

        return modified

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
            instrume = header["INSTRUME"].lower()
            if instrume == cls.supported_instrument.lower():
                return True
        return False

    @cache_translation
    def to_physical_filter(self):
        """Calculate the physical filter name.

        Returns
        -------
        filter : `str`
            Name of filter. Can be a combination of FILTER, FILTER1, and
            FILTER2 headers joined by a "~".  Trailing "~empty" components
            are stripped.
            Returns "unknown" if no filter is declared.
        """
        joined = super().to_physical_filter()
        while joined.endswith("~empty"):
            joined = joined.removesuffix("~empty")

        return joined

    @cache_translation
    def to_exposure_time(self):
        """Calculate the exposure time

        Returns
        -------
        exposure time : `float`
            Taken from the exposure time ROIMILLI (Region of Interest, in ms)
        Raises
        ------
        NotImplementedError
            Raised if ROIMILLI isn't in header
        """

        if self.is_key_ok("ROIMILLI"):
            return self.quantity_from_card("ROIMILLI", u.ms)
        else:
            raise NotImplementedError("Unable to determine exposure time")

    @cache_translation
    def to_datetime_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        for k in ["MJD-OBS", "MJD"]:
            if self.is_key_ok(k):
                self._used_these_cards(k)
                return Time(self._header[k], scale="tai", format="mjd")

        raise NotImplementedError("Unable to determine datetime_begin")

    @classmethod
    def observing_date_to_offset(cls, observing_date: astropy.time.Time) -> astropy.time.TimeDelta | None:
        """Return the offset to use when calculating the observing day.

        Parameters
        ----------
        observing_date : `astropy.time.Time`
            The date of the observation. Unused.

        Returns
        -------
        offset : `astropy.time.TimeDelta`
            The offset to apply. During lab testing the offset is Pacific
            Time which can mean UTC-7 or UTC-8 depending on daylight savings.
            In Chile the offset is always UTC-12.
        """
        # Timezone calculations are slow. Only do this if the instrument
        # is in the lab.
        if int(observing_date.strftime("%Y%m")) >= cls._CAMERA_SHIP_DATE:
            return cls._ROLLOVER_TIME  # 12 hours in base class

        # Convert the date to a datetime UTC.
        pacific_tz = pytz.timezone("US/Pacific")
        pacific_time = observing_date.utc.to_datetime(timezone=pacific_tz)

        # We need the offset to go the other way.
        offset = pacific_time.utcoffset() * -1
        return astropy.time.TimeDelta(offset)
