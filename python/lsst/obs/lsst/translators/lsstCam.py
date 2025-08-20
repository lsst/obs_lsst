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
from astropy.coordinates import Angle

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
        "exposure_time_requested": ("EXPTIME", dict(unit=u.s)),
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

    # Date we know camera is in Chile and potentially taking on-sky data.
    _CAMERA_ON_TELESCOPE_DATE = astropy.time.Time("2025-03-01T00:00", format="isot", scale="utc")

    # Not allowed to use obstype for can_see_sky fallback.
    _can_check_obstype_for_can_see_sky = False

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

        day_obs = header.get("DAYOBS")
        i_day_obs = int(day_obs) if day_obs else None
        if (
            day_obs in ("20231107", "20231108", "20241015", "20241016")
            and header["FILTER"] == "ph_05"
        ):
            header["FILTER"] = "ph_5"
            modified = True

        # For first ~ week of observing the ROTPA in the header was the ComCam
        # value and needed to be adjusted by 90 degrees to match LSSTCam.
        # Fixed for day_obs 20250422.
        rotpa_fixed_on_day = 20250422
        if i_day_obs and i_day_obs > 20250301 and i_day_obs < rotpa_fixed_on_day:
            if rotpa := header.get("ROTPA"):
                header["ROTPA"] = rotpa - 90.0
                modified = True
                log.debug("%s: Correcting ROTPA by -90.0", log_label)

        # For half a night the ROTPA was out by 180 degrees.
        if i_day_obs == 20250422:
            seq_num = header["SEQNUM"]
            if seq_num < 251 and (rotpa := header.get("ROTPA")):
                rotpa_corrected = rotpa - 180.0
                angle = Angle(rotpa_corrected * u.deg)
                header["ROTPA"] = float(angle.wrap_at("180d").value)
                modified = True
                log.debug(
                    "%s: Correcting ROTPA of %f by 180 degrees to %f", log_label, rotpa, header["ROTPA"]
                )

        # For the night of 20250518 the dome was closed but many
        # calibs had the wrong header because of dome/TMA faults.
        if i_day_obs == 20250518:
            if header["VIGN_MIN"] != "FULLY":
                header["VIGN_MIN"] = "FULLY"
                modified = True
                log.debug("%s: Correcting VIGN_MIN to FULLY", log_label)

        # DM-51847: For several nights in July, the dome was closed but many
        # flats had the wrong header because of a dome CSC regression
        fix_ranges = {
            20250703: [(743, 745)],
            20250704: [(832, 834)],
            20250705: [(1, 736)],
            20250707: [(784, 823), (744, 783), (864, 903), (904, 943)],
            20250714: [(258, 781)],
            20250715: [(205, 1218)],
            20250819: [(4, 1052)], # DM-52249
        }
        if i_day_obs in fix_ranges:
            i_seq_num = header["SEQNUM"]
            for seq_range in fix_ranges[i_day_obs]:
                if (seq_range[0] <= i_seq_num <= seq_range[1]
                    and header["VIGN_MIN"] != "FULLY"):
                    header["VIGN_MIN"] = "FULLY"
                    modified = True
                    log.debug("%s: Correcting VIGN_MIN to FULLY", log_label)

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

    def _is_on_mountain(self):
        """Indicate whether these data are coming from the instrument
        installed on the mountain.

        Returns
        -------
        is : `bool`
            `True` if instrument is on the mountain.

        Notes
        -----
        LSSTCam was installed on the Simonyi Telescope in March 2025.
        This flag is true even if the telescope is on the test stand or a
        simulated file has come from the BTS.
        """
        # phosim is always on mountain.
        if self._get_controller_code() == "H":
            return True

        date = self.to_datetime_begin()
        if date > self._CAMERA_ON_TELESCOPE_DATE:
            return True

        return False

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

    @cache_translation
    def to_exposure_time(self):
        # Use shutter time if greater than 0 (for a dark the shutter never
        # opens).
        if self.is_key_ok("SHUTTIME"):
            if (shuttime := self._header["SHUTTIME"]) > 0.0:
                return shuttime * u.s
        return self.to_exposure_time_requested()

    @cache_translation
    def to_can_see_sky(self) -> bool | None:
        if not self._is_on_mountain():
            # Lab data cannot see sky.
            return False
        return super().to_can_see_sky()
