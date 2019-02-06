# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation code for LSST simulations"""

__all__ = ("LsstSimTranslator", )

import warnings
import logging

import astropy.utils.exceptions
from astropy.time import Time
from astropy.coordinates import AltAz

from astro_metadata_translator import cache_translation, StubTranslator

from .lsst import LSST_LOCATION, read_detector_ids, compute_detector_exposure_id_generic

log = logging.getLogger(__name__)


class LsstSimTranslator(StubTranslator):
    """Shared routines for LSST Simulated Data.
    """
    cameraPolicyFile = None
    """Path to policy file relative to obs_lsst root."""

    detectorMapping = None
    """Mapping of detector name to detector number and serial."""

    detectorSerials = None
    """Mapping of detector serial number to raft, number, and name."""

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
        return compute_detector_exposure_id_generic(exposure_id, detector_num, max_num=1000,
                                                    mode="concat")

    @classmethod
    def detector_mapping(cls):
        """Returns the mapping of full name to detector ID and serial.

        Returns
        -------
        mapping : `dict` of `str`:`tuple`
            Returns the mapping of full detector name (group+detector)
            to detector number and serial.

        Notes
        -----
        Will construct the mapping if none has previously been constructed.
        """
        if cls.cameraPolicyFile is not None:
            if cls.detectorMapping is None:
                cls.detectorMapping = read_detector_ids(cls.cameraPolicyFile)

        return cls.detectorMapping

    @classmethod
    def detector_serials(cls):
        """Obtain the mapping of detector serial to detector group, name,
        and number.

        Returns
        -------
        info : `dict` of `tuple` of (`str`, `str`, `int`)
            A `dict` with the serial numbers as keys and values of detector
            group, name, and number.
        """
        if cls.detectorSerials is None:
            detector_mapping = cls.detector_mapping()

            if detector_mapping is not None:
                # Form mapping to go from serial number to names/numbers
                serials = {}
                for fullname, (id, serial) in cls.detectorMapping.items():
                    raft, detector_name = fullname.split("_")
                    serials[serial] = (raft, detector_name, id)
                cls.detectorSerials = serials
            else:
                raise RuntimeError("Unable to obtain detector mapping information")

        return cls.detectorSerials

    @classmethod
    def compute_detector_num_from_name(cls, detector_group, detector_name):
        """Helper method to return the detector number from the name.

        Parameters
        ----------
        detector_group : `str`
            Name of the detector grouping.  This is generally the raft name.
        detector_name : `str`
            Detector name.

        Returns
        -------
        num : `int`
            Detector number.
        """
        fullname = f"{detector_group}_{detector_name}"

        num = None
        detector_mapping = cls.detector_mapping()
        if detector_mapping is None:
            raise RuntimeError("Unable to obtain detector mapping information")

        if fullname in detector_mapping:
            num = detector_mapping[fullname]
        else:
            log.warning(f"Unable to determine detector number from detector name {fullname}")

        return num[0]

    @classmethod
    def compute_detector_info_from_serial(cls, detector_serial):
        """Helper method to return the detector information from the serial.

        Parameters
        ----------
        detector_serial : `str`
            Detector serial ID.

        Returns
        -------
        info : `tuple` of (`str`, `str`, `int`)
            Detector group, name, and number.
        """
        serial_mapping = cls.detector_serials()
        if serial_mapping is None:
            raise RuntimeError("Unable to obtain serial mapping information")

        if detector_serial in serial_mapping:
            info = serial_mapping[detector_serial]
        else:
            log.warning(f"Unable to determine detector information from detector serial {detector_serial}")

        return info

    @cache_translation
    def to_telescope(self):
        # Docstring will be inherited. Property defined in properties.py
        telescope = None
        if "OUTFILE" in self._header and self._header["OUTFILE"].startswith("lsst"):
            telescope = "LSST"
            self._used_these_cards("OUTFILE")
        elif "LSST_NUM" in self._header:
            telescope = "LSST"
            self._used_these_cards("LSST_NUM")
        return telescope

    @cache_translation
    def to_location(self):
        # Docstring will be inherited. Property defined in properties.py
        location = None
        tel = self.to_telescope()
        if tel == "LSST":
            location = LSST_LOCATION
        return location

    @cache_translation
    def to_datetime_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        self._used_these_cards("MJD-OBS")
        return Time(self._header["MJD-OBS"], scale="tai", format="mjd")

    @cache_translation
    def to_datetime_end(self):
        # Docstring will be inherited. Property defined in properties.py
        return self.to_datetime_begin() + self.to_exposure_time()

    @cache_translation
    def to_detector_num(self):
        # Docstring will be inherited. Property defined in properties.py
        raft = self.to_detector_group()
        detector = self.to_detector_name()
        return self.compute_detector_num_from_name(raft, detector)

    @cache_translation
    def to_detector_exposure_id(self):
        exposure_id = self.to_exposure_id()
        num = self.to_detector_num()
        return self.compute_detector_exposure_id(exposure_id, num)

    @cache_translation
    def to_observation_type(self):
        # Docstring will be inherited. Property defined in properties.py
        obstype = self._header["IMGTYPE"]
        self._used_these_cards("IMGTYPE")
        obstype = obstype.lower()
        if obstype == "skyexp":
            obstype = "science"
        return obstype

    @cache_translation
    def to_altaz_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        if self.to_observation_type() == "science":
            # Derive from RADec in absence of any other information
            radec = self.to_tracking_radec()
            if radec is not None:
                # This triggers warnings because of the future dates
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=astropy.utils.exceptions.AstropyWarning)
                    altaz = radec.transform_to(AltAz)
                return altaz
        return None
