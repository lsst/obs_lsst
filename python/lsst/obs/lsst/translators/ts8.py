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

from .lsst import LsstBaseTranslator

log = logging.getLogger(__name__)


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
    }

    _trivial_map = {
        "science_program": "RUNNUM",
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
    }

    DETECTOR_MAX = 250
    """Maximum number of detectors to use when calculating the
    detector_exposure_id."""

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

    @staticmethod
    def compute_exposure_id(dateobs, seqnum=0, controller=None):
        """Helper method to calculate the TS8 exposure_id.

        Parameters
        ----------
        dateobs : `str`
            Date of observation in FITS ISO format.
        seqnum : `int`, unused
            Sequence number. Ignored.
        controller : `str`, unused
            Controller type. Ignored.

        Returns
        -------
        exposure_id : `int`
            Exposure ID.
        """
        # There is worry that seconds are too coarse so use 10th of second
        # and read the first 21 characters.
        exposure_id = re.sub(r"\D", "", dateobs[:21])
        return int(exposure_id)

    @cache_translation
    def to_datetime_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        self._used_these_cards("MJD-OBS")
        return Time(self._header["MJD-OBS"], scale="utc", format="mjd")

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
        raise ValueError(f"RAFTNAME has unexpected form of '{raft_name}'")

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

        Uses the FILTPOS header.

        Returns
        -------
        filter : `str`
            The filter name.  Returns "NONE" if no filter can be determined.

        Notes
        -----
        The calculations here are examples rather than being accurate.
        They need to be fixed once the camera acquisition system does
        this properly.
        """

        try:
            filter_pos = self._header["FILTPOS"]
            self._used_these_cards("FILTPOS")
        except KeyError:
            log.warning("%s: FILTPOS key not found in header (assuming NONE)",
                        self.to_observation_id())
            return "NONE"

        try:
            return {
                2: 'g',
                3: 'r',
                4: 'i',
                5: 'z',
                6: 'y',
            }[filter_pos]
        except KeyError:
            log.warning("%s: Unknown filter position (assuming NONE): %d",
                        self.to_observation_id(), filter_pos)
            return "NONE"

    def to_exposure_id(self):
        """Generate a unique exposure ID number

        Note that SEQNUM is not unique for a given day in TS8 data
        so instead we convert the ISO date of observation directly to an
        integer.

        Returns
        -------
        exposure_id : `int`
            Unique exposure number.
        """
        iso = self._header["DATE-OBS"]
        self._used_these_cards("DATE-OBS")

        return self.compute_exposure_id(iso)

    # For now assume that visit IDs and exposure IDs are identical
    to_visit_id = to_exposure_id

    @cache_translation
    def to_observation_id(self):
        # Docstring will be inherited. Property defined in properties.py
        filename = self._header["FILENAME"]
        self._used_these_cards("FILENAME")
        return filename[:filename.rfind(".")]
