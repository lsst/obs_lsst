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
from astropy.time import Time

from astro_metadata_translator import cache_translation

from .lsst import compute_detector_exposure_id_generic, LsstBaseTranslator

log = logging.getLogger(__name__)


class LsstTS8Translator(LsstBaseTranslator):
    """Metadata translator for LSST Test Stand 8 data.
    """

    name = "LSST-TS8"
    """Name of this translation class"""

    _const_map = {
        # TS8 is not attached to a telescope so many translations are null.
        "telescope": "LSST",
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

    cameraPolicyFile = "policy/ts8.yaml"

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
                "CONTNUM" in header:
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
        return compute_detector_exposure_id_generic(exposure_id, detector_num, max_num=250,
                                                    mode="concat")

    @staticmethod
    def compute_exposure_id(dateobs, seqnum=0):
        """Helper method to calculate the TS8 exposure_id.

        Parameters
        ----------
        dateobs : `str`
            Date of observation in FITS ISO format.
        seqnum : `int`, unused
            Sequence number. Ignored.

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
    def to_instrument(self):
        """Calculate the instrument name.

        Returns
        -------
        instrume : `str`
            Name of the test stand.
        """
        return "LSST-TS8"

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
            log.warning("FILTPOS key not found in header (assuming NONE)")
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
            log.warning("Unknown filter position (assuming NONE): %d", filter_pos)
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
