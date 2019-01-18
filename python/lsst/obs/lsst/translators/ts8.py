# This file is part of obs_lsst.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Metadata translation code for LSST TestStand 8 headers"""

__all__ = ("LsstTS8Translator", )

import logging
import re

import astropy.units as u
from astropy.time import Time

from astro_metadata_translator import cache_translation, StubTranslator

from .lsst import TZERO, ROLLOVERTIME, compute_detector_exposure_id

log = logging.getLogger(__name__)


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
        "object": "NONE",
        "relative_humidity": None,
        "temperature": None,
        "pressure": None,
        "detector_group": "R00",  # Only a single raft
    }

    _trivial_map = {
        "science_program": "RUNNUM",
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
    }

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

        return ["S00", "S01", "S02",
                "S10", "S11", "S12",
                "S20", "S21", "S22"][detector]

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
        return compute_detector_exposure_id(exposure_id, num, max_num=10, mode="multiply")

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
        so instead we use the number of seconds since TZERO as defined in
        the main LSST part of the package.

        Returns
        -------
        exposure_id : `int`
            Unique exposure number.
        """

        nsec = self.to_datetime_begin() - ROLLOVERTIME - TZERO
        nsec.format = "sec"
        return int(nsec.value)

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
