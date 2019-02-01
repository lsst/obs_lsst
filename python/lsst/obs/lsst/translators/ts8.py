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

from astro_metadata_translator import cache_translation, StubTranslator

from .lsst import compute_detector_exposure_id_generic

log = logging.getLogger(__name__)

# Define the group name for TS8 globally so that it can be used
# in multiple places. There is only a single raft.
_DETECTOR_GROUP_NAME = "R00"


class LsstTS8Translator(StubTranslator):
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
        "detector_group": _DETECTOR_GROUP_NAME,
    }

    _trivial_map = {
        "science_program": "RUNNUM",
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
    }

    DETECTOR_GROUP_NAME = _DETECTOR_GROUP_NAME
    """Fixed name of detector group."""

    _detector_names = ["S00", "S01", "S02",
                       "S10", "S11", "S12",
                       "S20", "S21", "S22"]
    """Detector names in detector number order."""

    @classmethod
    def can_translate(cls, header, filename=None):
        """Indicate whether this translation class can translate the
        supplied header.

        There is no ``INSTRUME`` header in TS8 data. Instead we use
        the ``TSTAND`` header. We also look at the file name to see if
        it starts with "ts8-".

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
        return cls.can_translate_with_options(header, {"TSTAND": "TS8"}, filename=filename)

    @classmethod
    def compute_detector_num_from_name(cls, detector_name):
        """Helper method to return the detector number from the name.

        Parameters
        ----------
        detector_name : `str`
            Detector name.

        Returns
        -------
        num : `int`
            Detector number.

        Raises
        ------
        ValueError
            The supplied name is not known.
        """
        return cls._detector_names.index(detector_name)

    @classmethod
    def compute_detector_name_from_num(cls, detector_num):
        """Helper method to return the detector name from the number.

        Parameters
        ----------
        detector_num : `int`
            Detector number.

        Returns
        -------
        name : `str`
            Detector name.

        Raises
        ------
        IndexError
            The supplied index is out of range.
        TypeError
            The supplied index is not an `int`.
        """
        return cls._detector_names[detector_num]

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
        return compute_detector_exposure_id_generic(exposure_id, detector_num, max_num=10,
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
            Name of the test stand and raft combination.
            For example: "TS8-RTM-001"
        """
        raft = self._to_raft_name()
        return f"TS8-{raft}"

    @cache_translation
    def to_datetime_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        self._used_these_cards("MJD-OBS")
        return Time(self._header["MJD-OBS"], scale="utc", format="mjd")

    @cache_translation
    def to_datetime_end(self):
        # Docstring will be inherited. Property defined in properties.py
        return self.to_datetime_begin() + self.to_exposure_time()

    @cache_translation
    def to_dark_time(self):
        """Calculate the dark time.

        If a DARKTIME header is not found, the value is assumed to be
        identical to the exposure time.

        Returns
        -------
        dark : `astropy.units.Quantity`
            The dark time in seconds.
        """
        if "DARKTIME" in self._header:
            darktime = self._header("DARKTIME")*u.s
        else:
            log.warning("Unable to determine dark time. Setting from exposure time.")
            darktime = self.to_exposure_time()
        return darktime

    @cache_translation
    def to_detector_name(self):
        # Docstring will be inherited. Property defined in properties.py
        detector = self.to_detector_num()
        return self.compute_detector_name_from_num(detector)

    def _to_raft_name(self):
        """Returns the full name of the raft.

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

        # this seems to be appended more or less at random and should be removed.
        serial = re.sub("-Dev$", "", serial)
        return serial

    @cache_translation
    def to_detector_num(self):
        """Return value of detector_num from headers.

        Unique (for instrument) integer identifier for the sensor.
        Calculated from the raftname.

        Returns
        -------
        detector_num : `int`
            The translated property.
        """
        raft_name = self._to_raft_name()
        serial = self.to_detector_serial()

        # a dict of dicts holding the raft serials
        raft_serial_data = {
            'RTM-002': {  # config for RTM-004 aka ETU #1
                'ITL-3800C-023': 0,  # S00
                'ITL-3800C-032': 1,  # S01
                'ITL-3800C-042': 2,  # S02
                'ITL-3800C-090': 3,  # S10
                'ITL-3800C-107': 4,  # S11
                'ITL-3800C-007': 5,  # S12
                'ITL-3800C-004': 6,  # S20
                'ITL-3800C-139': 7,  # S21
                'ITL-3800C-013': 8   # S22
            },
            'RTM-003': {  # config for RTM-004 aka ETU #2
                'ITL-3800C-145': 0,  # S00
                'ITL-3800C-022': 1,  # S01
                'ITL-3800C-041': 2,  # S02
                'ITL-3800C-100': 3,  # S10
                'ITL-3800C-017': 4,  # S11
                'ITL-3800C-018': 5,  # S12
                'ITL-3800C-102': 6,  # S20
                'ITL-3800C-146': 7,  # S21
                'ITL-3800C-103': 8   # S22
            },
            'RTM-004': {  # config for RTM-004 aka RTM #1
                'ITL-3800C-381': 0,  # S00
                'ITL-3800C-333': 1,  # S01
                'ITL-3800C-380': 2,  # S02
                'ITL-3800C-346': 3,  # S10
                'ITL-3800C-062': 4,  # S11
                'ITL-3800C-371': 5,  # S12
                'ITL-3800C-385': 6,  # S20
                'ITL-3800C-424': 7,  # S21
                'ITL-3800C-247': 8   # S22
            },
            'RTM-005': {  # config for RTM-005 aka RTM #2
                'E2V-CCD250-220': 0,  # S00
                'E2V-CCD250-239': 1,  # S01
                'E2V-CCD250-154': 2,  # S02
                'E2V-CCD250-165': 3,  # S10
                'E2V-CCD250-130': 4,  # S11
                'E2V-CCD250-153': 5,  # S12
                'E2V-CCD250-163': 6,  # S20
                'E2V-CCD250-216': 7,  # S21
                'E2V-CCD250-252': 8   # S22
            },
            'RTM-006': {  # config for RTM-006 aka RTM #3
                'E2V-CCD250-229': 0,  # S00
                'E2V-CCD250-225': 1,  # S01
                'E2V-CCD250-141': 2,  # S02
                'E2V-CCD250-221': 3,  # S10
                'E2V-CCD250-131': 4,  # S11
                'E2V-CCD250-190': 5,  # S12
                'E2V-CCD250-211': 6,  # S20
                'E2V-CCD250-192': 7,  # S21
                'E2V-CCD250-217': 8   # S22
            },
            'RTM-007': {  # config for RTM-007 aka RTM #4
                'E2V-CCD250-260': 0,  # S00
                'E2V-CCD250-182': 1,  # S01
                'E2V-CCD250-175': 2,  # S02
                'E2V-CCD250-167': 3,  # S10
                'E2V-CCD250-195': 4,  # S11
                'E2V-CCD250-201': 5,  # S12
                'E2V-CCD250-222': 6,  # S20
                'E2V-CCD250-213': 7,  # S21
                'E2V-CCD250-177': 8   # S22
            },
            'RTM-008': {  # config for RTM-008 aka RTM #5
                'E2V-CCD250-160': 0,  # S00
                'E2V-CCD250-208': 1,  # S01
                'E2V-CCD250-256': 2,  # S02
                'E2V-CCD250-253': 3,  # S10
                'E2V-CCD250-194': 4,  # S11
                'E2V-CCD250-231': 5,  # S12
                'E2V-CCD250-224': 6,  # S20
                'E2V-CCD250-189': 7,  # S21
                'E2V-CCD250-134': 8   # S22
            },
            'RTM-010': {  # config for RTM-010 aka RTM #7
                'E2V-CCD250-266': 0,  # S00
                'E2V-CCD250-268': 1,  # S01
                'E2V-CCD250-200': 2,  # S02
                'E2V-CCD250-273': 3,  # S10
                'E2V-CCD250-179': 4,  # S11
                'E2V-CCD250-263': 5,  # S12
                'E2V-CCD250-226': 6,  # S20
                'E2V-CCD250-264': 7,  # S21
                'E2V-CCD250-137': 8,  # S22
            },
            'RTM-011': {  # config for RTM-011 aka RTM #8 NB Confluence lies here, values are from the data!
                'ITL-3800C-083': 0,  # S00
                'ITL-3800C-172': 1,  # S01
                'ITL-3800C-142': 2,  # S02
                'ITL-3800C-173': 3,  # S10
                'ITL-3800C-136': 4,  # S11
                'ITL-3800C-227': 5,  # S12
                'ITL-3800C-226': 6,  # S20
                'ITL-3800C-230': 7,  # S21
                'ITL-3800C-235': 8,  # S22
            },
            'RTM-012': {  # config for RTM-012 aka RTM #9
                'E2V-CCD250-281': 0,  # S00
                'E2V-CCD250-237': 1,  # S01
                'E2V-CCD250-234': 2,  # S02
                'E2V-CCD250-277': 3,  # S10
                'E2V-CCD250-251': 4,  # S11
                'E2V-CCD250-149': 5,  # S12
                'E2V-CCD250-166': 6,  # S20
                'E2V-CCD250-214': 7,  # S21
                'E2V-CCD250-228': 8,  # S22
            },
            'RTM-014': {  # config for RTM-014 aka RTM #11
                'ITL-3800C-307': 0,  # S00
                'ITL-3800C-325': 1,  # S01
                'ITL-3800C-427': 2,  # S02
                'ITL-3800C-361': 3,  # S10
                'ITL-3800C-440': 4,  # S11
                'ITL-3800C-411': 5,  # S12
                'ITL-3800C-400': 6,  # S20
                'ITL-3800C-455': 7,  # S21
                'ITL-3800C-407': 8,  # S22
            }
        }
        return raft_serial_data[raft_name][serial]

    @cache_translation
    def to_detector_exposure_id(self):
        # Docstring will be inherited. Property defined in properties.py
        exposure_id = self.to_exposure_id()
        num = self.to_detector_num()
        return self.compute_detector_exposure_id(exposure_id, num)

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

    @cache_translation
    def to_observation_type(self):
        # Docstring will be inherited. Property defined in properties.py
        obstype = self._header["IMGTYPE"]
        self._used_these_cards("IMGTYPE")
        return obstype.lower()
