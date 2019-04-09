# This file is currently part of obs_lsst but is written to allow it
# to be migrated to the astro_metadata_translator package at a later date.
#
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the LICENSE file in this directory for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

"""Metadata translation support code for LSST headers"""

__all__ = ("ROLLOVERTIME", "TZERO", "LSST_LOCATION", "read_detector_ids",
           "compute_detector_exposure_id_generic", "LsstBaseTranslator")

import os.path
import yaml
import logging

import astropy.units as u
from astropy.time import Time, TimeDelta
from astropy.coordinates import EarthLocation

from lsst.utils import getPackageDir

from astro_metadata_translator import cache_translation, FitsTranslator

# LSST day clock starts at UTC+8
ROLLOVERTIME = TimeDelta(8*60*60, scale="tai", format="sec")
TZERO = Time("2010-01-01T00:00", format="isot", scale="utc")

# LSST Default location in the absence of headers
LSST_LOCATION = EarthLocation.from_geodetic(-30.244639, -70.749417, 2663.0)

obs_lsst_packageDir = getPackageDir("obs_lsst")

log = logging.getLogger(__name__)


def read_detector_ids(policyFile):
    """Read a camera policy file and retrieve the mapping from CCD name
    to ID.

    Parameters
    ----------
    policyFile : `str`
        Name of YAML policy file to read, relative to the obs_lsst
        package.

    Returns
    -------
    mapping : `dict` of `str` to (`int`, `str`)
        A `dict` with keys being the full names of the detectors, and the
        value is a `tuple` containing the integer detector number and the
        detector serial number.

    Notes
    -----
    Reads the camera YAML definition file directly and extracts just the
    IDs and serials.  This routine does not use the standard
    `~lsst.obs.base.yamlCamera.YAMLCamera` infrastructure or
    `lsst.afw.cameraGeom`.  This is because the translators are intended to
    have minimal dependencies on LSST infrastructure.
    """

    file = os.path.join(obs_lsst_packageDir, policyFile)
    try:
        with open(file) as fh:
            # Use the fast parser since these files are large
            camera = yaml.load(fh, Loader=yaml.CSafeLoader)
    except OSError as e:
        raise ValueError(f"Could not load camera policy file {file}") from e

    mapping = {}
    for ccd, value in camera["CCDs"].items():
        mapping[ccd] = (int(value["id"]), value["serial"])

    return mapping


def compute_detector_exposure_id_generic(exposure_id, detector_num, max_num=1000, mode="concat"):
    """Compute the detector_exposure_id from the exposure id and the
    detector number.

    Parameters
    ----------
    exposure_id : `int`
        The exposure ID.
    detector_num : `int`
        The detector number.
    max_num : `int`, optional
        Maximum number of detectors to make space for. Defaults to 1000.
    mode : `str`, optional
        Computation mode. Defaults to "concat".
        - concat : Concatenate the exposure ID and detector number, making
                   sure that there is space for max_num and zero padding.
        - multiply : Multiply the exposure ID by the maximum detector
                     number and add the detector number.

    Returns
    -------
    detector_exposure_id : `int`
        Computed ID.

    Raises
    ------
    ValueError
        The detector number is out of range.
    """

    if detector_num is None:
        raise ValueError("Detector number must be defined.")
    if detector_num >= max_num or detector_num < 0:
        raise ValueError(f"Detector number out of range 0 <= {detector_num} <= {max_num}")

    if mode == "concat":
        npad = len(str(max_num))
        return int(f"{exposure_id}{detector_num:0{npad}d}")
    elif mode == "multiply":
        return max_num*exposure_id + detector_num
    else:
        raise ValueError(f"Computation mode of '{mode}' is not understood")


class LsstBaseTranslator(FitsTranslator):
    """Translation methods useful for all LSST-style headers."""

    _const_map = {}
    _trivial_map = {}

    # Do not specify a name for this translator
    cameraPolicyFile = None
    """Path to policy file relative to obs_lsst root."""

    detectorMapping = None
    """Mapping of detector name to detector number and serial."""

    detectorSerials = None
    """Mapping of detector serial number to raft, number, and name."""

    def search_paths(self):
        """Search paths to use for LSST data when looking for header correction
        files.

        Returns
        -------
        path : `list`
            List with a single element containing the full path to the
            ``corrections`` directory within the ``obs_lsst`` package.
        """
        return [os.path.join(obs_lsst_packageDir, "corrections")]

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
        return compute_detector_exposure_id_generic(exposure_id, detector_num, max_num=999,
                                                    mode="concat")

    @classmethod
    def detector_mapping(cls):
        """Returns the mapping of full name to detector ID and serial.

        Returns
        -------
        mapping : `dict` of `str`:`tuple`
            Returns the mapping of full detector name (group+detector)
            to detector number and serial.

        Raises
        ------
        ValueError
            Raised if no camera policy file has been registered with this
            translation class.

        Notes
        -----
        Will construct the mapping if none has previously been constructed.
        """
        if cls.cameraPolicyFile is not None:
            if cls.detectorMapping is None:
                cls.detectorMapping = read_detector_ids(cls.cameraPolicyFile)
        else:
            raise ValueError(f"Translation class '{cls.__name__}' has no registered camera policy file")

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
                    if serial in serials:
                        raise RuntimeError(f"Serial {serial} is defined in multiple places")
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
            return None

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
            raise RuntimeError("Unable to determine detector information from detector serial"
                               f" {detector_serial}")

        return info

    @staticmethod
    def compute_exposure_id(dayobs, seqnum):
        """Helper method to calculate the AuxTel exposure_id.

        Parameters
        ----------
        dayobs : `str`
            Day of observation in either YYYYMMDD or YYYY-MM-DD format.
        seqnum : `int` or `str`
            Sequence number.

        Returns
        -------
        exposure_id : `int`
            Exposure ID in form YYYYMMDDnnnnn form.
        """
        dayobs = dayobs.replace("-", "")

        if len(dayobs) != 8:
            raise ValueError(f"Malformed dayobs: {dayobs}")

        # Expect no more than 99,999 exposures in a day
        maxdigits = 5
        if seqnum >= 10**maxdigits:
            raise ValueError(f"Sequence number ({seqnum}) exceeds limit")

        # Form the number as a string zero padding the sequence number
        idstr = f"{dayobs}{seqnum:0{maxdigits}d}"
        return int(idstr)

    def _is_on_mountain(self):
        """Indicate whether these data are coming from the instrument
        installed on the mountain.

        Returns
        -------
        is : `bool`
            `True` if instrument is on the mountain.
        """
        if "TSTAND" in self._header:
            return False
        return True

    @cache_translation
    def to_location(self):
        # Docstring will be inherited. Property defined in properties.py
        location = None
        if not self._is_on_mountain():
            return location
        try:
            # Try standard FITS headers
            return super().to_location()
        except KeyError:
            return LSST_LOCATION

    @cache_translation
    def to_datetime_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        self._used_these_cards("MJD-OBS")
        return Time(self._header["MJD-OBS"], scale="tai", format="mjd")

    @cache_translation
    def to_datetime_end(self):
        # Docstring will be inherited. Property defined in properties.py
        if self.is_key_ok("DATE-END"):
            return super().to_datetime_end()

        return self.to_datetime_begin() + self.to_exposure_time()

    @cache_translation
    def to_detector_num(self):
        # Docstring will be inherited. Property defined in properties.py
        raft = self.to_detector_group()
        detector = self.to_detector_name()
        return self.compute_detector_num_from_name(raft, detector)

    @cache_translation
    def to_detector_exposure_id(self):
        # Docstring will be inherited. Property defined in properties.py
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
    def to_dark_time(self):
        """Calculate the dark time.

        If a DARKTIME header is not found, the value is assumed to be
        identical to the exposure time.

        Returns
        -------
        dark : `astropy.units.Quantity`
            The dark time in seconds.
        """
        if self.is_key_ok("DARKTIME"):
            darktime = self._header("DARKTIME")*u.s
        else:
            log.warning("Unable to determine dark time. Setting from exposure time.")
            darktime = self.to_exposure_time()
        return darktime

    @cache_translation
    def to_exposure_id(self):
        """Generate a unique exposure ID number

        This is a combination of DAYOBS and SEQNUM.

        Returns
        -------
        exposure_id : `int`
            Unique exposure number.
        """
        if "CALIB_ID" in self._header:
            self._used_these_cards("CALIB_ID")
            return None

        dayobs = self._header["DAYOBS"]
        seqnum = self._header["SEQNUM"]
        self._used_these_cards("DAYOBS", "SEQNUM")

        return self.compute_exposure_id(dayobs, seqnum)

    # For now "visits" are defined to be identical to exposures.
    to_visit_id = to_exposure_id

    @cache_translation
    def to_physical_filter(self):
        """Calculate the physical filter name.

        Returns
        -------
        filter : `str`
            Name of filter. Can be a combination of FILTER, FILTER1 and FILTER2
            headers joined by a "+".  Returns "NONE" if no filter is declared.
        """
        joined = self._join_keyword_values(["FILTER", "FILTER1", "FILTER2"], delim="+")
        if not joined:
            joined = "NONE"

        return joined
