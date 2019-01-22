import datetime
import re
from lsst.pipe.tasks.ingest import ParseTask
from lsst.pipe.tasks.ingestCalibs import CalibsParseTask
from astro_metadata_translator import ObservationInfo
import lsst.log as lsstLog
from . import LsstCam
from .translators.lsst import ROLLOVERTIME as MDROLLOVERTIME

EXTENSIONS = ["fits", "gz", "fz"]  # Filename extensions to strip off

# This is needed elsewhere and should only be defined in one place
# roll over at 8am UTC
ROLLOVERTIME = datetime.timedelta(hours=8)
TZERO = datetime.datetime(2010, 1, 1, tzinfo=datetime.timezone.utc)

__all__ = ["LsstCamParseTask", "ROLLOVERTIME", "TZERO"]


class LsstCamParseTask(ParseTask):
    """Parser suitable for lsstCam data.

    See https://docushare.lsstcorp.org/docushare/dsweb/Get/Version-43119/FITS_Raft.pdf
    """

    camera = None                       # class-scope camera to avoid instantiating once per file
    _cameraClass = LsstCam              # the class to instantiate for the class-scope camera
    _translatorClass = None

    def __init__(self, config, *args, **kwargs):
        super().__init__(config, *args, **kwargs)

        self.observationInfo = None
        if self.camera is None:
            self.camera = self._cameraClass()

    def getInfoFromMetadata(self, md, info=None):
        """Attempt to pull the desired information out of the header.

        Notes
        -----

        This is done through two mechanisms:

        * translation: a property is set directly from the relevant header keyword
        * translator: a property is set with the result of calling a method

        The translator methods receive the header metadata and should return the
        appropriate value, or None if the value cannot be determined.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList`
            FITS header
        info : `dict`, optional
            File properties, to be supplemented

        Returns
        -------
        info : `dict`
            Updated information.
        """
        # Always calculate a new ObservationInfo since getInfo calls
        # this method repeatedly for each header.
        self.observationInfo = ObservationInfo(md, translator_class=self._translatorClass,
                                               pedantic=False)

        info = super().getInfoFromMetadata(md, info)
        self.observationInfo = None
        return info

    def translate_wavelength(self, md):
        """Translate wavelength provided by teststand readout.

        The teststand driving script asks for a wavelength, and then reads the value back to ensure that
        the correct position was moved to. This number is therefore read back with sub-nm precision.
        Typically the position is within 0.005nm of the desired position, so we warn if it's not very
        close to an integer value.

        Future users should be aware that the HIERARCH MONOCH-WAVELENG key is NOT the requested value, and
        therefore cannot be used as a cross-check that the wavelength was close to the one requested.
        The only record of the wavelength that was set is in the original filename.

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            image metadata

        Returns
        -------
        wavelength : `int`
            The recorded wavelength as an int
        """
        raw_wl = md.getScalar("MONOWL")
        wl = int(round(raw_wl))
        if abs(raw_wl-wl) >= 0.1:
            logger = lsstLog.Log.getLogger('obs.lsst.ingest')
            logger.warn(
                'Translated significantly non-integer wavelength; '
                '%s is more than 0.1nm from an integer value', raw_wl)
        return wl

    def translate_dateObs(self, md):
        """Convert DATE-OBS to a legal format; TSEIA-83

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            image metadata

        Returns
        -------
        dateObs : `str`
            The date that the data was taken, e.g. 2018-08-20T21:56:24.608
        """
        dateObs = self.observationInfo.datetime_begin
        dateObs.format = "isot"
        return str(dateObs)

    translate_date = translate_dateObs

    def translate_dayObs(self, md):
        """Generate the day that the observation was taken

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            image metadata

        Returns
        -------
        dayObs : `str`
            The day that the data was taken, e.g. 1958-02-05
        """
        dateObs = self.observationInfo.datetime_begin
        dateObs -= MDROLLOVERTIME
        dateObs.format = "iso"
        dateObs.out_subfmt = "date"  # YYYY-MM-DD format
        return str(dateObs)

    def translate_snap(self, md):
        """Extract snap from metadata.

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            image metadata

        Returns
        -------
        snap : `int`
            snap number (default: 0)
        """
        try:
            return int(md.getScalar("SNAP"))
        except KeyError:
            return 0

    def translate_detectorName(self, md):
        """Extract ccd ID from CHIPID.

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            image metadata

        Returns
        -------
        ccdID : `str`
            name of ccd, e.g. S01
        """
        return self.observationInfo.detector_name

    def translate_raftName(self, md):
        """Extract raft ID from CHIPID.

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            image metadata

        Returns
        -------
        raftID : `str`
            name of raft, e.g. R21
        """
        return self.observationInfo.detector_group

    def translate_detector(self, md):
        """Extract detector number from raft and detector name.

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            image metadata

        Returns
        -------
        detID : `str`
            detector ID, e.g. 4
        """
        return self.observationInfo.detector_num

    def translate_expTime(self, md):
        return self.observationInfo.exposure_time.value

    def translate_object(self, md):
        return self.observationInfo.object

    def translate_imageType(self, md):
        obstype = self.observationInfo.observation_type.upper()
        # Dictionary for obstype values is not yet clear
        if obstype == "SCIENCE":
            obstype = "SKYEXP"
        return obstype

    def translate_filter(self, md):
        return self.observationInfo.physical_filter

    def translate_lsstSerial(self, md):
        return self.observationInfo.detector_serial

    def translate_run(self, md):
        return self.observationInfo.science_program

    def translate_visit(self, md):
        return self.observationInfo.visit_id

#############################################################################################################


class LsstCamCalibsParseTask(CalibsParseTask):
    """Parser for calibs."""

    def _translateFromCalibId(self, field, md):
        """Get a value from the CALIB_ID written by constructCalibs."""
        data = md.getScalar("CALIB_ID")
        match = re.search(r".*%s=(\S+)" % field, data)
        return match.groups()[0]

    def translate_raftName(self, md):
        return self._translateFromCalibId("raftName", md)

    def translate_detectorName(self, md):
        return self._translateFromCalibId("detectorName", md)

    def translate_detector(self, md):
        # this is not a _great_ fix, but this obs_package is enforcing that detectors be integers
        # and there's not an elegant way of ensuring this is the right type really
        return int(self._translateFromCalibId("detector", md))

    def translate_filter(self, md):
        return self._translateFromCalibId("filter", md)

    def translate_calibDate(self, md):
        return self._translateFromCalibId("calibDate", md)
