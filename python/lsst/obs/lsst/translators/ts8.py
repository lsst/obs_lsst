# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for LSST TestStand 8 headers"""

__all__ = ("LsstTS8Translator", )

import logging
import re

import astropy.units as u
from astropy.time import Time, TimeDelta

from astro_metadata_translator import cache_translation

from .lsst import LsstBaseTranslator, compute_detector_exposure_id_generic

log = logging.getLogger(__name__)

# First observation with new exposure ID is TS_C_20230524_000906.
_EXPOSURE_ID_DATE_CHANGE = Time("2023-05-24T23:00:00.0", format="isot", scale="tai")
_UNMODIFIED_DATE_OBS_HEADER = "HIERARCH LSST-TS8 DATE-OBS"


class LsstTS8Translator(LsstBaseTranslator):
    """Metadata translator for LSST Test Stand 8 data.
    """

    name = "LSST-TS8"
    """Name of this translation class"""

    _const_map = {
        # TS8 is not attached to a telescope so many translations are null.
        "instrument": "LSST-TS8",
        "telescope": None,
        "location": None,
        "boresight_rotation_coord": None,
        "boresight_rotation_angle": None,
        "boresight_airmass": None,
        "tracking_radec": None,
        "altaz_begin": None,
        "object": "UNKNOWN",
        "relative_humidity": None,
        "temperature": None,
        "pressure": None,
        "can_see_sky": False,
    }

    _trivial_map = {
        "science_program": "RUNNUM",
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
    }

    cameraPolicyFile = "policy/ts8.yaml"

    _ROLLOVER_TIME = TimeDelta(8*60*60, scale="tai", format="sec")
    """Time delta for the definition of a Rubin Test Stand start of day."""

    @classmethod
    def can_translate(cls, header, filename=None):
        """Indicate whether this translation class can translate the
        supplied header.

        There is no ``INSTRUME`` header in TS8 data. Instead we use
        the ``TSTAND`` header. We also look at the file name to see if
        it starts with "ts8-".

        Older data has no ``TSTAND`` header so we must use a combination
        of headers.

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
        can = cls.can_translate_with_options(header, {"TSTAND": "TS8"}, filename=filename)
        if can:
            return True

        if "LSST_NUM" in header and "REBNAME" in header and \
                "CONTNUM" in header and \
                header["CONTNUM"] in ("000018910e0c", "000018ee33b7", "000018ee0f35", "000018ee3b40",
                                      "00001891fcc7", "000018edfd65", "0000123b5ba8", "000018911b05",
                                      "00001891fa3e", "000018910d7f", "000018ed9f12", "000018edf4a7",
                                      "000018ee34e6", "000018ef1464", "000018eda120", "000018edf8a2",
                                      "000018ef3819", "000018ed9486", "000018ee02c8", "000018edfb24",
                                      "000018ee34c0", "000018edfb51", "0000123b51d1", "0000123b5862",
                                      "0000123b8ca9", "0000189208fa", "0000189111af", "0000189126e1",
                                      "000018ee0618", "000018ee3b78", "000018ef1534"):
            return True

        return False

    @classmethod
    def fix_header(cls, header, instrument, obsid, filename=None):
        """Fix TS8 headers.

        Notes
        -----
        See `~astro_metadata_translator.fix_header` for details of the general
        process.
        """
        modified = False

        # Calculate the standard label to use for log messages
        log_label = cls._construct_log_prefix(obsid, filename)

        if header.get("DATE-OBS", "OBS") == header.get("DATE-TRG", "TRG"):
            log.warning("%s: DATE-OBS detected referring to end of observation.", log_label)
            if "DATE-END" not in header:
                header["DATE-END"] = header["DATE-OBS"]
                header["MJD-END"] = header["MJD-OBS"]

            # Time system used to be UTC and at some point became TAI.
            # Need to include the transition date and update the TIMESYS
            # header.
            timesys = header.get("TIMESYS", "utc").lower()

            # Need to subtract exposure time from DATE-OBS.
            date_obs = None
            for (key, format) in (("MJD-OBS", "mjd"), ("DATE-OBS", "isot")):
                if date_val := header.get(key):
                    date_obs = Time(date_val, format=format, scale=timesys)
                    break

            if date_obs:
                # The historical exposure ID calculation requires that we
                # have access to the unmodified DATE-OBS value.
                header[_UNMODIFIED_DATE_OBS_HEADER] = header["DATE-OBS"]

                exptime = TimeDelta(header["EXPTIME"]*u.s, scale="tai")
                date_obs = date_obs - exptime
                header["MJD-OBS"] = float(date_obs.mjd)
                header["DATE-OBS"] = date_obs.isot
                header["DATE-BEG"] = header["DATE-OBS"]
                header["MJD-BEG"] = header["MJD-OBS"]

                modified = True
            else:
                # This should never happen because DATE-OBS is already present.
                log.warning("%s: Unexpectedly failed to extract date from DATE-OBS/MJD-OBS", log_label)

        return modified

    @classmethod
    def compute_detector_exposure_id(cls, exposure_id, detector_num):
        # Docstring inherited from LsstBaseTranslator.
        return compute_detector_exposure_id_generic(exposure_id, detector_num, max_num=cls.DETECTOR_MAX)

    @classmethod
    def max_exposure_id(cls):
        """The maximum exposure ID expected from this instrument.

        The TS8 implementation is non-standard because TS8 data can create
        two different forms of exposure_id based on the date but we need
        the largest form to be the one returned.

        Returns
        -------
        max_exposure_id : `int`
            The maximum value.
        """
        max_date = "2050-12-31T23:59.999"
        return int(re.sub(r"\D", "", max_date[:21]))

    @cache_translation
    def to_detector_name(self):
        # Docstring will be inherited. Property defined in properties.py
        serial = self.to_detector_serial()
        detector_info = self.compute_detector_info_from_serial(serial)
        return detector_info[1]

    def to_detector_group(self):
        """Returns the name of the raft.

        Extracted from RAFTNAME header.

        Raftname should be of the form: 'LCA-11021_RTM-011-Dev' and
        the resulting name will have the form "RTM-NNN".

        Returns
        -------
        name : `str`
            Name of raft.
        """
        raft_name = self._header["RAFTNAME"]
        self._used_these_cards("RAFTNAME")
        match = re.search(r"(RTM-\d\d\d)", raft_name)
        if match:
            return match.group(0)
        raise ValueError(f"{self._log_prefix}: RAFTNAME has unexpected form of '{raft_name}'")

    @cache_translation
    def to_detector_serial(self):
        """Returns the serial number of the detector.

        Returns
        -------
        serial : `str`
            LSST assigned serial number.

        Notes
        -----
        This is the LSST assigned serial number (``LSST_NUM``), and not
        the manufacturer's serial number (``CCD_SERN``).
        """
        serial = self._header["LSST_NUM"]
        self._used_these_cards("LSST_NUM")

        # this seems to be appended more or less at random and should be
        # removed.
        serial = re.sub("-Dev$", "", serial)
        return serial

    @cache_translation
    def to_physical_filter(self):
        """Return the filter name.

        Uses the FILTPOS header for older TS8 data.  Newer data can use
        the base class implementation.

        Returns
        -------
        filter : `str`
            The filter name.  Returns "NONE" if no filter can be determined.

        Notes
        -----
        The FILTPOS handling is retained for backwards compatibility.
        """

        default = "unknown"
        try:
            filter_pos = self._header["FILTPOS"]
            self._used_these_cards("FILTPOS")
            if filter_pos is None:
                raise KeyError
        except KeyError:
            # TS8 data from 2023-05-09 and later should be following
            # DM-38882 conventions.
            physical_filter = super().to_physical_filter()
            # Some TS8 taken prior to 2023-05-09 have the string
            # 'unspecified' as the FILTER keyword and don't really
            # follow any established convention.
            if 'unspecified' in physical_filter:
                return default
            return physical_filter

        try:
            return {
                2: 'g',
                3: 'r',
                4: 'i',
                5: 'z',
                6: 'y',
            }[filter_pos]
        except KeyError:
            log.warning("%s: Unknown filter position (assuming %s): %d",
                        self._log_prefix, default, filter_pos)
        return default

    @cache_translation
    def to_exposure_id(self):
        """Generate a unique exposure ID number

        Modern TS8 data conforms to standard LSSTCam OBSID, using the "C"
        controller variant (all TS8 uses "C" controller). Due to existing
        ingests, data taken before 2023-05-25 must use the old style
        timestamp ID.

        For older data SEQNUM is not unique for a given day in TS8 data
        so instead we convert the ISO date of observation directly to an
        integer.

        Returns
        -------
        exposure_id : `int`
            Unique exposure number.
        """
        begin = self.to_datetime_begin()

        if begin > _EXPOSURE_ID_DATE_CHANGE:
            obsid = self.to_observation_id()
            if obsid.startswith("TS_C_"):
                return super().to_exposure_id()

        iso = self._header.get(_UNMODIFIED_DATE_OBS_HEADER, self._header["DATE-OBS"])
        self._used_these_cards("DATE-OBS")

        # There is worry that seconds are too coarse so use 10th of second
        # and read the first 21 characters.
        exposure_id = re.sub(r"\D", "", iso[:21])
        return int(exposure_id)

    # For now assume that visit IDs and exposure IDs are identical
    to_visit_id = to_exposure_id

    @cache_translation
    def to_observation_id(self):
        # Docstring will be inherited. Property defined in properties.py
        if self.is_key_ok("OBSID"):
            observation_id = self._header["OBSID"]
            self._used_these_cards("OBSID")
            return observation_id
        filename = self._header["FILENAME"]
        self._used_these_cards("FILENAME")
        return filename[:filename.rfind(".")]
