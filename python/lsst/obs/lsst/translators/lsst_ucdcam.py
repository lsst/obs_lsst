# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for LSST UCDavis Test Stand headers"""

__all__ = ("LsstUCDCamTranslator", )

import logging
import re
import os.path

import astropy.units as u
from astropy.time import Time

from astro_metadata_translator import cache_translation, StubTranslator

from .lsst import compute_detector_exposure_id_generic

log = logging.getLogger(__name__)

# There is only one detector name used
_DETECTOR_NAME = "S00"


class LsstUCDCamTranslator(StubTranslator):
    """Metadata translator for LSST UC Davis test camera data.

    This instrument is a test system for individual LSST CCDs.
    To fit this instrument into the standard naming convention for LSST
    instruments we use a fixed detector name (S00) and assign a different
    raft name to each detector.  The detector number changes for each CCD.
    """

    name = "LSST-UCDCam"
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
        "detector_name": _DETECTOR_NAME,
    }

    _trivial_map = {
        "exposure_time": ("EXPTIME", dict(unit=u.s)),
    }

    DETECTOR_NAME = _DETECTOR_NAME
    """Fixed name of single sensor in raft."""

    _detector_map = {
        "E2V-CCD250-112-04": (0, "R00"),
        "ITL-3800C-029": (1, "R01"),
        "ITL-3800C-002": (2, "R02"),
    }
    """Map detector serial to raft and detector number.  Eventually the
    detector number will come out of the policy camera definition."""

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
        # Check 3 headers that all have to match
        for k, v in (("ORIGIN", "UCDAVIS"), ("INSTRUME", "SAO"), ("TSTAND", "LSST_OPTICAL_SIMULATOR")):
            if k not in header:
                return False
            if header[k] != v:
                return False
        return True

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
        return compute_detector_exposure_id_generic(exposure_id, detector_num, max_num=3,
                                                    mode="concat")

    @staticmethod
    def compute_exposure_id(dateobs, seqnum=0):
        """Helper method to calculate the exposure_id.

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
        # Use 1 second resolution
        exposure_id = re.sub(r"\D", "", dateobs[:19])
        return int(exposure_id)

    @cache_translation
    def to_instrument(self):
        """Calculate the instrument name.

        Returns
        -------
        instrume : `str`
            Name of the test stand.  We do not distinguish between ITL and
            E2V.
        """
        return self.name

    @cache_translation
    def to_datetime_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        self._used_these_cards("MJD")
        mjd = float(self._header["MJD"])  # Header uses a FITS string
        return Time(mjd, scale="utc", format="mjd")

    @cache_translation
    def to_datetime_end(self):
        # Docstring will be inherited. Property defined in properties.py
        return self.to_datetime_begin() + self.to_exposure_time()

    @cache_translation
    def to_detector_num(self):
        """Determine the number associated with this detector.

        Returns
        -------
        num : `int`
            The number of the detector.  Each CCD gets a different number.
        """
        serial = self.to_detector_serial()
        return self._detector_map[serial][0]

    @cache_translation
    def to_detector_group(self):
        """Determine the pseudo raft name associated with this detector.

        Returns
        -------
        raft : `str`
            The name of the raft.  The raft is derived from the serial number
            of the detector.
        """
        serial = self.to_detector_serial()
        return self._detector_map[serial][1]

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
    def to_detector_serial(self):
        """Returns the serial number of the detector.

        Returns
        -------
        serial : `str`
            LSST assigned serial number.

        Notes
        -----
        This is the LSST assigned serial number (``LSST_NUM``), and not
        necessarily the manufacturer's serial number (``CCD_SERN``).
        """
        serial = self._header["LSST_NUM"]
        self._used_these_cards("LSST_NUM")
        return serial

    @cache_translation
    def to_detector_exposure_id(self):
        # Docstring will be inherited. Property defined in properties.py
        exposure_id = self.to_exposure_id()
        num = self.to_detector_num()
        return self.compute_detector_exposure_id(exposure_id, num)

    @cache_translation
    def to_physical_filter(self):
        """Return the filter name.

        Uses the FILTER header.

        Returns
        -------
        filter : `str`
            The filter name.  Returns "NONE" if no filter can be determined.
        """

        if "FILTER" in self._header:
            self._used_these_cards("FILTER")
            return self._header["FILTER"].lower()
        else:
            log.warning("FILTER key not found in header (assuming NONE)")
            return "NONE"

    def to_exposure_id(self):
        """Generate a unique exposure ID number

        Note that SEQNUM is not unique for a given day
        so instead we convert the ISO date of observation directly to an
        integer.

        Returns
        -------
        exposure_id : `int`
            Unique exposure number.
        """
        date = self.to_datetime_begin()
        return self.compute_exposure_id(date.isot)

    # For now assume that visit IDs and exposure IDs are identical
    to_visit_id = to_exposure_id

    @cache_translation
    def to_observation_id(self):
        # Docstring will be inherited. Property defined in properties.py
        filename = self._header["FILENAME"]
        self._used_these_cards("FILENAME")
        return os.path.splitext(os.path.basename(filename))[0]

    @cache_translation
    def to_observation_type(self):
        # Docstring will be inherited. Property defined in properties.py
        obstype = self._header["IMGTYPE"]
        self._used_these_cards("IMGTYPE")
        return obstype.lower()

    @cache_translation
    def to_science_program(self):
        """Calculate the run number for this observation.

        There is no explicit run header, so instead treat each day
        as the run in YYYY-MM-DD format.

        Returns
        ------
        run : `str`
            YYYY-MM-DD string corresponding to the date of observation.
        """
        # Get a copy so that we can edit the default formatting
        date = self.to_datetime_begin().copy()
        date.format = "iso"
        date.out_subfmt = "date"  # YYYY-MM-DD format
        return str(date)
