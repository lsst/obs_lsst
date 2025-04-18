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

__all__ = ("TZERO", "SIMONYI_LOCATION", "read_detector_ids",
           "compute_detector_exposure_id_generic", "LsstBaseTranslator",
           "SIMONYI_TELESCOPE")

import os.path
import yaml
import logging
import re
import datetime
import hashlib

import astropy.coordinates
import astropy.units as u
from astropy.time import Time, TimeDelta
from astropy.coordinates import EarthLocation

from lsst.utils import getPackageDir

from astro_metadata_translator import cache_translation, FitsTranslator
from astro_metadata_translator.translators.helpers import tracking_from_degree_headers, \
    altaz_from_degree_headers


TZERO = Time("2015-01-01T00:00", format="isot", scale="utc")
TZERO_DATETIME = TZERO.to_datetime()

# Delimiter to use for multiple filters/gratings
FILTER_DELIMITER = "~"

# Regex to use for parsing a GROUPID string
GROUP_RE = re.compile(r"^(\d\d\d\d\-\d\d\-\d\dT\d\d:\d\d:\d\d)\.(\d\d\d)(?:[\+#](\d+))?$")

# LSST Default location in the absence of headers
SIMONYI_LOCATION = EarthLocation.from_geodetic(-70.749417, -30.244639, 2663.0)

# Name of the main survey telescope
SIMONYI_TELESCOPE = "Simonyi Survey Telescope"

# Supported controller codes.
# The order here directly relates to the resulting exposure ID
# calculation. Do not reorder. Add new ones to the end.
# OCS, CCS, pHosim, P for simulated OCS, Q for simulated CCS, S for
# simulated images.
SIMULATED_CONTROLLERS = "HPQS"
CONTROLLERS = "OC" + SIMULATED_CONTROLLERS

# Number of decimal digits allocated to the sequence number in exposure_ids.
_SEQNUM_MAXDIGITS = 5

# Number of decimal digits allocated to the day of observation (and controller
# code) in exposure_ids.
_DAYOBS_MAXDIGITS = 8

# Value added to day_obs for controllers after the default.
_CONTROLLER_INCREMENT = 1000_00_00

# Number of decimal digits used by exposure_ids.
EXPOSURE_ID_MAXDIGITS = _SEQNUM_MAXDIGITS + _DAYOBS_MAXDIGITS

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


def compute_detector_exposure_id_generic(exposure_id, detector_num, max_num):
    """Compute the detector_exposure_id from the exposure id and the
    detector number.

    Parameters
    ----------
    exposure_id : `int`
        The exposure ID.
    detector_num : `int`
        The detector number.
    max_num : `int`
        Maximum number of detectors to make space for.

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
        raise ValueError(f"Detector number out of range 0 <= {detector_num} < {max_num}")

    return max_num*exposure_id + detector_num


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

    DETECTOR_MAX = 1000
    """Maximum number of detectors to use when calculating the
    detector_exposure_id.

    Note that because this is the maximum number *of* detectors, for
    zero-based ``detector_num`` values this is one greater than the maximum
    ``detector_num``.  It is also often rounded up to the nearest power of
    10 anyway, to allow ``detector_exposure_id`` values to be easily decoded by
    humans.
    """

    _DEFAULT_LOCATION = SIMONYI_LOCATION
    """Default telescope location in absence of relevant FITS headers."""

    _ROLLOVER_TIME = TimeDelta(12*60*60, scale="tai", format="sec")
    """Time delta for the definition of a Rubin Observatory start of day.
    Used when the header is missing. See LSE-400 or SITCOMTN-032 for details.
    """

    _non_sky_observation_types: tuple[str, ...] = ("bias", "dark", "flat")
    """Observation types that correspond to an observation where the detector
    can not see sky photons.
    """

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """Ensure that subclasses clear their own detector mapping entries
        such that subclasses of translators that use detector mappings
        do not pick up the incorrect values from a parent."""

        cls.detectorMapping = None
        cls.detectorSerials = None

        super().__init_subclass__(**kwargs)

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
            The offset to apply. The default implementation returns a fixed
            number but subclasses can return a different value depending
            on whether the instrument is in the instrument lab or on the
            mountain.
        """
        return cls._ROLLOVER_TIME

    @classmethod
    def compute_detector_exposure_id(cls, exposure_id, detector_num):
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
        from .._packer import RubinDimensionPacker

        config = RubinDimensionPacker.ConfigClass()
        config.use_controllers()
        return RubinDimensionPacker.pack_id_pair(exposure_id, detector_num, config=config)

    @classmethod
    def max_detector_exposure_id(cls):
        """The maximum detector exposure ID expected to be generated by
        this instrument.

        Returns
        -------
        max_id : `int`
            The maximum value.
        """
        max_exposure_id = cls.max_exposure_id()
        # We subtract 1 from DETECTOR_MAX because LSST detector_num values are
        # zero-based, and detector_max is the maximum number *of* detectors,
        # while this returns the (inclusive) maximum ID value.
        return cls.compute_detector_exposure_id(max_exposure_id, cls.DETECTOR_MAX - 1)

    @classmethod
    def max_exposure_id(cls):
        """The maximum exposure ID expected from this instrument.

        Returns
        -------
        max_exposure_id : `int`
            The maximum value.

        Notes
        -----
        The value is hard-coded to reflect historical values that were used
        for various controllers before the sequence counter was unified.
        """
        # Assumes maximum observing date of 2050-12-31, 99,999 exposures per
        # day and 6 controllers.
        return 7050123199999

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
    def compute_exposure_id(dayobs, seqnum, controller=None):
        """Helper method to calculate the exposure_id.

        Parameters
        ----------
        dayobs : `str` or `int`
            Day of observation in either YYYYMMDD or YYYY-MM-DD format.
            If the string looks like ISO format it will be truncated before the
            ``T`` before being handled.
        seqnum : `int` or `str`
            Sequence number.
        controller : `str`, optional
            Controller to use. If this is "O", no change is made to the
            exposure ID. Before Oct 5 2023, if it is "C" a 1000 is added to the
            year component of the exposure ID. If it is "H" a 2000 is added to
            the year component. Before Apr 18 2025, this sequence continues
            with "P", "Q", and "S" controllers. `None` indicates that the
            controller is not relevant to the exposure ID calculation
            (generally this is the case for test stand data).

        Returns
        -------
        exposure_id : `int`
            Exposure ID in form YYYYMMDDnnnnn form.
        """
        if isinstance(seqnum, str):
            seqnum = int(seqnum)
        # We really want an integer but the checks require a str.
        if isinstance(dayobs, int):
            dayobs = str(dayobs)

        if "T" in dayobs:
            dayobs = dayobs[:dayobs.find("T")]

        dayobs = dayobs.replace("-", "")

        if len(dayobs) != 8:
            raise ValueError(f"Malformed dayobs: {dayobs}")

        # Expect no more than 99,999 exposures in a day
        if seqnum >= 10**_SEQNUM_MAXDIGITS:
            raise ValueError(f"Sequence number ({seqnum}) exceeds limit")

        dayobs = int(dayobs)
        if dayobs > 20231004 and controller == "C":
            # As of this date the CCS controller has a unified counter
            # with the OCS, so there is no need to adjust the dayobs
            # to make unique exposure IDs.
            controller = None
        elif dayobs > 20250417 and controller in {"P", "S", "Q"}:
            # At some point in the past the PSQ and OC controller sequence
            # counters were unified. To avoid confusion with previous files
            # that may already be ingested where we do not want to change
            # the exposure ID, only assume identical sequences from this date.
            controller = None

        # Camera control changes the exposure ID
        if controller is not None:
            index = CONTROLLERS.find(controller)
            if index == -1:
                raise ValueError(f"Supplied controller, '{controller}' is not "
                                 f"in supported list: {CONTROLLERS}")

            # Increment a thousand years per controller
            dayobs += _CONTROLLER_INCREMENT * index

        # Form the number as a string zero padding the sequence number
        idstr = f"{dayobs}{seqnum:0{_SEQNUM_MAXDIGITS}d}"

        # Exposure ID has to be an integer
        return int(idstr)

    @staticmethod
    def unpack_exposure_id(exposure_id):
        """Unpack an exposure ID into dayobs, seqnum, and controller.

        Parameters
        ----------
        exposure_id : `int`
            Integer exposure ID produced by `compute_exposure_id`.

        Returns
        -------
        dayobs : `str`
            Day of observation as a YYYYMMDD string.
        seqnum : `int`
            Sequence number.
        controller : `str`
            Controller code.  Will be ``O`` (but should be ignored) for IDs
            produced by calling `compute_exposure_id` with ``controller=None``.
        """
        dayobs, seqnum = divmod(exposure_id, 10**_SEQNUM_MAXDIGITS)
        controller_index = dayobs // _CONTROLLER_INCREMENT - 2
        dayobs -= controller_index * _CONTROLLER_INCREMENT
        return (str(dayobs), seqnum, CONTROLLERS[controller_index], )

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

    def is_on_sky(self):
        """Determine if this is an on-sky observation.

        Returns
        -------
        is_on_sky : `bool`
            Returns True if this is a observation on sky on the
            summit.
        """
        # For LSST we think on sky unless tracksys is local
        if self.is_key_ok("TRACKSYS"):
            if self._header["TRACKSYS"].lower() == "local":
                # not on sky
                return False

        # These are obviously not on sky
        if self.to_observation_type() in self._non_sky_observation_types:
            return False

        return self._is_on_mountain()

    @cache_translation
    def to_location(self):
        # Docstring will be inherited. Property defined in properties.py
        if not self._is_on_mountain():
            return None
        try:
            # Try standard FITS headers
            return super().to_location()
        except (KeyError, TypeError):
            return self._DEFAULT_LOCATION

    @cache_translation
    def to_datetime_begin(self):
        # Docstring will be inherited. Property defined in properties.py
        # Prefer -BEG over -OBS. Let it fail with KeyError if no headers
        # can be found.
        date_key = "MJD-BEG"
        date_fmt = "mjd"
        for k in ("MJD-BEG", "DATE-BEG", "MJD-OBS", "DATE-OBS"):
            if self.is_key_ok(k):
                date_key = k
                date_fmt = "mjd" if k.startswith("MJD") else "fits"
                break

        self._used_these_cards(date_key)
        return Time(self._header[date_key], scale="tai", format=date_fmt)

    @cache_translation
    def to_datetime_end(self):
        # Docstring will be inherited. Property defined in properties.py
        if self.is_key_ok("DATE-END"):
            return super().to_datetime_end()

        exposure_time = self.to_exposure_time()
        if exposure_time.value < 0.0:
            # Some translators deliberately return -1.0s if the exposure
            # time can not be determined. In that scenario set end time
            # to the same value as the start time.
            return self.to_datetime_begin()

        return self.to_datetime_begin() + exposure_time

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
        if obstype in ("skyexp", "object"):
            obstype = "science"
        return obstype

    @cache_translation
    def to_observation_reason(self):
        # Docstring will be inherited. Property defined in properties.py
        for key in ("REASON", "TESTTYPE"):
            if self.is_key_ok(key):
                reason = self._header[key]
                self._used_these_cards(key)
                return reason.lower()
        # no specific header present so use the default translation
        return super().to_observation_reason()

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
            darktime = self._header["DARKTIME"]*u.s
            self._used_these_cards("DARKTIME")
        else:
            log.warning("%s: Unable to determine dark time. Setting from exposure time.",
                        self._log_prefix)
            darktime = self.to_exposure_time()
        return darktime

    def _get_controller_code(self) -> str | None:
        """Return the controller code.

        Returns
        -------
        code : `str`
            Single character code representing the controller. Returns
            `None` if no controller can be determined.
        """
        key = "CONTRLLR"
        if self.is_key_ok(key):
            controller = self._header[key]
            self._used_these_cards(key)
        else:
            controller = None
        return controller

    @cache_translation
    def to_exposure_id(self):
        """Generate a unique exposure ID number

        This is a combination of DAYOBS and SEQNUM, and optionally
        CONTRLLR.

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

        controller = self._get_controller_code()

        return self.compute_exposure_id(dayobs, seqnum, controller=controller)

    @cache_translation
    def to_visit_id(self):
        """Calculate the visit associated with this exposure.

        Notes
        -----
        For LATISS and LSSTCam the default visit is derived from the
        exposure group.  For other instruments we return the exposure_id.
        """

        exposure_group = self.to_exposure_group()
        # If the group is an int we return it
        try:
            visit_id = int(exposure_group)
            return visit_id
        except ValueError:
            pass

        # A Group is defined as ISO date with an extension
        # The integer must be the same for a given group so we can never
        # use datetime_begin.
        # Nominally a GROUPID looks like "ISODATE+N" where the +N is
        # optional.  This can be converted to seconds since epoch with
        # an adjustment for N.
        # For early data lacking that form we hash the group and return
        # the int.
        matches_date = GROUP_RE.match(exposure_group)
        if matches_date:
            iso_str = matches_date.group(1)
            fraction = matches_date.group(2)
            n = matches_date.group(3)
            if n is not None:
                n = int(n)
            else:
                n = 0
            iso = datetime.datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S")

            tdelta = iso - TZERO_DATETIME
            epoch = int(tdelta.total_seconds())

            # Form the integer from EPOCH + 3 DIGIT FRAC + 0-pad N
            visit_id = int(f"{epoch}{fraction}{n:04d}")
        else:
            # Non-standard string so convert to numbers
            # using a hash function. Use the first N hex digits
            group_bytes = exposure_group.encode("us-ascii")
            hasher = hashlib.blake2b(group_bytes)
            # Need to be big enough it does not possibly clash with the
            # date-based version above
            digest = hasher.hexdigest()[:14]
            visit_id = int(digest, base=16)

            # To help with hash collision, append the string length
            visit_id = int(f"{visit_id}{len(exposure_group):02d}")

        return visit_id

    @cache_translation
    def to_physical_filter(self):
        """Calculate the physical filter name.

        Returns
        -------
        filter : `str`
            Name of filter. Can be a combination of FILTER, FILTER1 and FILTER2
            headers joined by a "~". Returns "unknown" if no filter is declared
        """
        joined = self._join_keyword_values(["FILTER", "FILTER1", "FILTER2"], delim=FILTER_DELIMITER)
        if not joined:
            joined = "unknown"

        # Replace instances of "NONE" with "none".
        joined = joined.replace("NONE", "none")

        return joined

    @cache_translation
    def to_tracking_radec(self):
        # Do not even attempt to attach an RA/Dec for observations that we
        # know are not going to be tracking. The Rubin OCS can sometimes
        # report the telescope is tracking when it's not when doing
        # calibrations like these. Darks are sometimes taken whilst tracking
        # to test stability so those are special-cased.
        non_sky_obstypes = {t for t in self._non_sky_observation_types if t != "dark"}
        if self.to_observation_type() in non_sky_obstypes:
            return None

        # Not an observation that is tracking in RA/Dec so it is not
        # appropriate to report a value for this.
        if self.are_keys_ok(["TRACKSYS"]) and self._header["TRACKSYS"] != "RADEC":
            return None

        # RA/DEC are *derived* headers and for the case where the DATE-BEG
        # is 1970 they are garbage and should not be used.
        try:
            if self._header["DATE-OBS"] == self._header["DATE"]:
                # A fixed up date -- use AZEL as source of truth
                altaz = self.to_altaz_begin()
                radec = astropy.coordinates.SkyCoord(altaz.transform_to(astropy.coordinates.ICRS()),
                                                     obstime=altaz.obstime,
                                                     location=altaz.location)
            else:
                radecsys = ("RADESYS",)
                radecpairs = (("RASTART", "DECSTART"), ("RA", "DEC"))
                radec = tracking_from_degree_headers(self, radecsys, radecpairs)
        except Exception:
            # If this observation was not formally on sky then we are allowed
            # to return None.
            if self.is_on_sky():
                raise
            radec = None

        return radec

    @cache_translation
    def to_altaz_begin(self):
        if not self._is_on_mountain():
            return None

        # H controller data are sometimes science observations without
        # having AZSTART header. The code lets those return nothing.
        if self._get_controller_code() == "H" and not self.are_keys_ok(["ELSTART", "AZSTART"]):
            return None

        # Always attempt to find the alt/az values regardless of observation
        # type.
        return altaz_from_degree_headers(self, (("ELSTART", "AZSTART"),),
                                         self.to_datetime_begin(), is_zd=False, max_alt=95.55, min_alt=-5.55)

    @cache_translation
    def to_exposure_group(self):
        """Calculate the exposure group string.

        For LSSTCam and LATISS this is read from the ``GROUPID`` header.
        If that header is missing the exposure_id is returned instead as
        a string.
        """
        if self.is_key_ok("GROUPID"):
            exposure_group = self._header["GROUPID"]
            self._used_these_cards("GROUPID")
            return exposure_group
        return super().to_exposure_group()

    @cache_translation
    def to_focus_z(self):
        """Return the defocal distance of the camera in units of mm.
        If there is no ``FOCUSZ`` value in the header it will return
        the default 0.0mm value.

        Returns
        -------
        focus_z: `astropy.units.Quantity`
            The defocal distance from header in mm or the 0.0mm default
        """
        if self.is_key_ok("FOCUSZ"):
            # Some broken files have strings instead of floats.
            focus_z = float(self._header["FOCUSZ"])
            return focus_z * u.mm
        return super().to_focus_z()

    @staticmethod
    def _is_filter_empty(filter):
        """Return true if the supplied filter indicates an empty filter slot

        Parameters
        ----------
        filter : `str`
            The filter string to check.

        Returns
        -------
        is_empty : `bool`
            `True` if the filter string looks like it is referring to an
            empty filter slot. For example this can be if the filter is
            "empty" or "empty_2".
        """
        return bool(re.match(r"empty_?\d*$", filter.lower()))

    def _determine_primary_filter(self):
        """Determine the primary filter from the ``FILTER`` header.

        Returns
        -------
        filter : `str`
            The contents of the ``FILTER`` header with some appropriate
            defaulting.
        """

        if self.is_key_ok("FILTER"):
            physical_filter = self._header["FILTER"]
            self._used_these_cards("FILTER")

            if self._is_filter_empty(physical_filter):
                physical_filter = "empty"
        else:
            # Be explicit about having no knowledge of the filter
            # by setting it to "unknown". It should always have a value.
            physical_filter = "unknown"

            # Warn if the filter being unknown is important
            obstype = self.to_observation_type()
            if obstype not in ("bias", "dark"):
                log.warning("%s: Unable to determine the filter",
                            self._log_prefix)

        return physical_filter

    @cache_translation
    def to_observing_day(self):
        """Return the day of observation as YYYYMMDD integer.

        For LSSTCam and other compliant instruments this is the value
        of the DAYOBS header.

        Returns
        -------
        obs_day : `int`
            The day of observation.
        """
        if self.is_key_ok("DAYOBS"):
            self._used_these_cards("DAYOBS")
            return int(self._header["DAYOBS"])

        return super().to_observing_day()

    @cache_translation
    def to_observation_counter(self):
        """Return the sequence number within the observing day.

        Returns
        -------
        counter : `int`
            The sequence number for this day.
        """
        if self.is_key_ok("SEQNUM"):
            # Some older LATISS data may not have the header
            # but this is corrected in fix_header for LATISS.
            self._used_these_cards("SEQNUM")
            return int(self._header["SEQNUM"])

        # This indicates a problem so we warn and return a 0
        log.warning("%s: Unable to determine the observation counter so returning 0",
                    self._log_prefix)
        return 0

    @cache_translation
    def to_boresight_rotation_coord(self):
        """Boresight rotation angle.

        Only relevant for science observations.
        """
        unknown = "unknown"
        if not self.is_on_sky():
            return unknown

        self._used_these_cards("ROTCOORD")
        coord = self._header.get("ROTCOORD", unknown)
        if coord is None:
            coord = unknown
        return coord

    @cache_translation
    def to_boresight_airmass(self):
        """Calculate airmass at boresight at start of observation.

        Notes
        -----
        Early data are missing AMSTART header so we fall back to calculating
        it from ELSTART.
        """
        if not self.is_on_sky():
            return None

        # This observation should have AMSTART
        amkey = "AMSTART"
        if self.is_key_ok(amkey):
            self._used_these_cards(amkey)
            return self._header[amkey]

        # Instead we need to look at azel
        altaz = self.to_altaz_begin()
        if altaz is not None:
            return altaz.secz.to_value()

        log.warning("%s: Unable to determine airmass of a science observation, returning 1.",
                    self._log_prefix)
        return 1.0

    @cache_translation
    def to_group_counter_start(self):
        # Effectively the start of the visit as determined by the headers.
        counter = self.to_observation_counter()
        # Older data does not have the CURINDEX header.
        if self.is_key_ok("CURINDEX"):
            # CURINDEX is 1-based.
            seq_start = counter - self._header["CURINDEX"] + 1
            self._used_these_cards("CURINDEX")
            return seq_start
        else:
            # If the counter is 0 we need to pick something else
            # that is not going to confuse the visit calculation
            # (since setting everything to 0 will make one big visit).
            return counter if counter != 0 else self.to_exposure_id()

    @cache_translation
    def to_group_counter_end(self):
        # Effectively the end of the visit as determined by the headers.
        counter = self.to_observation_counter()
        # Older data does not have the CURINDEX or MAXINDEX headers.
        if self.is_key_ok("CURINDEX") and self.is_key_ok("MAXINDEX"):
            # CURINDEX is 1-based. CURINDEX == MAXINDEX indicates the
            # final exposure in the sequence.
            remaining = self._header["MAXINDEX"] - self._header["CURINDEX"]
            seq_end = counter + remaining
            self._used_these_cards("CURINDEX", "MAXINDEX")
            return seq_end
        else:
            # If the counter is 0 we need to pick something else
            # that is not going to confuse the visit calculation
            # (since setting everything to 0 will make one big visit).
            return counter if counter != 0 else self.to_exposure_id()

    @cache_translation
    def to_has_simulated_content(self):
        # Check all the simulation flags.
        # We do not know all the simulation flags that we may have so
        # must check every header key. Ideally HIERARCH SIMULATE would
        # be a hierarchical header so _header["SIMULATE"] would return
        # everything. The header looks like:
        #
        # HIERARCH SIMULATE ATMCS =      / ATMCS Simulation Mode
        # HIERARCH SIMULATE ATHEXAPOD = 0 / ATHexapod Simulation Mode
        # HIERARCH SIMULATE ATPNEUMATICS =   / ATPneumatics Simulation Mode
        # HIERARCH SIMULATE ATDOME =   1 / ATDome Simulation Mode
        # HIERARCH SIMULATE ATSPECTROGRAPH = 0 / ATSpectrograph Simulation Mode
        #
        # So any header that includes "SIMULATE" in the key name and has a
        # true value implies that something in the data is simulated.
        for k, v in self._header.items():
            if "SIMULATE" in k and v:
                self._used_these_cards(k)
                return True

        # If the controller is H, P, S, or Q then the data are simulated.
        controller = self._get_controller_code()
        if controller:
            if controller in SIMULATED_CONTROLLERS:
                return True

        # No simulation flags set.
        return False

    @cache_translation
    def to_relative_humidity(self) -> float | None:
        key = "HUMIDITY"
        if self.is_key_ok(key):
            self._used_these_cards(key)
            return self._header[key]

        return None

    @cache_translation
    def to_pressure(self):
        key = "PRESSURE"
        if self.is_key_ok(key):
            value = self._header[key]
            self._used_these_cards(key)
            # There has been an inconsistency in units for the pressure reading
            # so we need to adjust for this.
            if value > 10_000:
                unit = u.Pa
            else:
                unit = u.hPa
            return value * unit

        return None

    @cache_translation
    def to_temperature(self):
        key = "AIRTEMP"
        if self.is_key_ok(key):
            self._used_these_cards(key)
            return self._header[key] * u.deg_C
        return None

    @cache_translation
    def to_can_see_sky(self) -> bool | None:
        key = "SHUTTIME"
        if self.is_key_ok(key) and self._header[key] == 0.0:
            # Shutter never opened so impossible to see sky.
            self._used_these_cards(key)
            return False

        key = "VIGN_MIN"
        if self.is_key_ok(key):
            self._used_these_cards(key)
            vignetted = self._header[key]
            if vignetted == "FULLY":
                return False
            return True

        # Fallback to using the observation type if the key is missing.
        # May not want to allow this for non-simulated cameras after
        # comcam goes on sky.
        return super().to_can_see_sky()
