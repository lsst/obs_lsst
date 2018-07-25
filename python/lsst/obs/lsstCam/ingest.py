import os
import re
import lsst.pex.exceptions as pexExcept
from lsst.pipe.tasks.ingest import ParseTask
from lsst.pipe.tasks.ingestCalibs import CalibsParseTask
import lsst.log as lsstLog
from lsst.obs.lsstCam import lsstCam

EXTENSIONS = ["fits", "gz", "fz"]  # Filename extensions to strip off

camera = lsstCam.LsstCam()  # Global camera to avoid instantiating once per file

class LsstCamParseTask(ParseTask):
    """Parser suitable for lsstCam data.

    See https://docushare.lsstcorp.org/docushare/dsweb/Get/Version-43119/FITS_Raft.pdf
    """

    def __init__(self, config, *args, **kwargs):
        super(ParseTask, self).__init__(config, *args, **kwargs)

    def XXX_getInfo(self, filename):
        """Get the basename and other data which is only available from the filename/path.

        This seems fragile, but this is how the teststand data will *always* be written out,
        as the software has been "frozen" as they are now in production mode.

        Parameters
        ----------
        filename : `str`
            The filename

        Returns
        -------
        phuInfo : `dict`
            Dictionary containing the header keys defined in the ingest config from the primary HDU
        infoList : `list`
            A list of dictionaries containing the phuInfo(s) for the various extensions in MEF files
        """
        phuInfo, infoList = ParseTask.getInfo(self, filename)

        pathname, basename = os.path.split(filename)
        basename = re.sub(r"\.(%s)$" % "|".join(EXTENSIONS), "", basename)
        phuInfo['basename'] = basename

        # Now pull the acq type & jobID from the path (no, they're not in the header)
        # the acq type is the type of test, eg flat/fe55/darks etc
        # jobID is the test number, and corresponds to database entries in the eTraveller/cameraTestDB
        pathComponents = pathname.split("/")
        if len(pathComponents) < 0:
            raise RuntimeError("Path %s is too short to deduce raftID" % pathname)
        raftId, runId, acquisitionType, testVersion, jobId, sensorLocationInRaft = pathComponents[-6:]
        if runId != phuInfo['run']:
            raise RuntimeError("Expected runId %s, found %s from path %s" % phuInfo['run'], runId, pathname)

        phuInfo['raftId'] = raftId  # also in the header - RAFTNAME
        phuInfo['field'] = acquisitionType  # NOT in the header
        phuInfo['jobId'] = int(jobId)  # NOT in the header
        phuInfo['raft'] = 'R00'
        phuInfo['ccd'] = sensorLocationInRaft  # NOT in the header

        return phuInfo, infoList

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
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        wavelength : `int`
            The recorded wavelength as an int
        """
        raw_wl = md.get("MONOWL")
        wl = int(round(raw_wl))
        if abs(raw_wl-wl) >= 0.1:
            logger = lsstLog.Log.getLogger('obs.lsstCam.ingest')
            logger.warn(
                'Translated significantly non-integer wavelength; '
                '%s is more than 0.1nm from an integer value', raw_wl)
        return wl

    def translate_dayObs(self, md):
        """Generate the day that the observation was taken

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        dayObs : `str`
            The day that the data was taken, e.g. 1958-02-05
        """
        return md.get("DATE-OBS")[:10]

    def XXX_translate_visit(self, md):
        """Generate a unique visit from the timestamp.

        It might be better to use the 1000*runNo + seqNo, but the latter isn't currently set

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        visit_num : `int`
            Visit number, as translated
        """
        mjd = md.get("MJD-OBS")
        mmjd = mjd - 55197              # relative to 2010-01-01, just to make the visits a tiny bit smaller
        return int(1e5*mmjd)            # 86400s per day, so we need this resolution

    def translate_snap(self, md):
        """Extract snap from metadata.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        snap : `int`
            snap number (default: 0)
        """
        try:
            return int(md.get("SNAP"))
        except pexExcept.NotFoundError:
            return 0

    def translate_detectorName(self, md):
        """Extract ccd ID from CHIPID.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        ccdID : `str`
            name of ccd, e.g. S01
        """
        return md.get("CHIPID")[4:]

    def translate_raftName(self, md):
        """Extract raft ID from CHIPID.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        raftID : `str`
            name of raft, e.g. R21
        """
        return md.get("CHIPID")[:3]

    def translate_detector(self, md):
        """Extract raft ID from CHIPID.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        raftID : `str`
            name of raft, e.g. R21
        """
        global camera  # avoids (very slow) instantiation for each file

        raftName = self.translate_raftName(md)
        detectorName = self.translate_detectorName(md)
        fullName = '_'.join([raftName, detectorName])
        detId = camera._nameDetectorDict[fullName].getId()

        return detId

#############################################################################################################


class LsstCamCalibsParseTask(CalibsParseTask):
    """Parser for calibs."""

    def _translateFromCalibId(self, field, md):
        """Get a value from the CALIB_ID written by constructCalibs."""
        data = md.get("CALIB_ID")
        match = re.search(".*%s=(\S+)" % field, data)
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

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

class AuxTelParseTask(LsstCamParseTask):
    """Parser suitable for auxTel data.

    We need this because as of 2018-07-20 the headers are essentially empty and
    there's information we need from the filename, so we need to override getInfo
    and provide some translation methods
    """

    def getInfo(self, filename):
        """Get the basename and other data which is only available from the filename/path.

        This is horribly fragile!

        Parameters
        ----------
        filename : `str`
            The filename

        Returns
        -------
        phuInfo : `dict`
            Dictionary containing the header keys defined in the ingest config from the primary HDU
        infoList : `list`
            A list of dictionaries containing the phuInfo(s) for the various extensions in MEF files
        """
        phuInfo, infoList = ParseTask.getInfo(self, filename)

        pathname, basename = os.path.split(filename)
        basename = re.sub(r"\.(%s)$" % "|".join(EXTENSIONS), "", basename)
        phuInfo['basename'] = basename

        # Now pull the imageType and the correct exposure time the path (no, they're not in the header)

        basenameComponents = basename.split("_")
        try:
            imageType = basenameComponents[1]
            expTime = float(basenameComponents[2])
        except IndexError:
            raise RuntimeError("File basename %s is too short to deduce expTime" % basename)

        phuInfo['imageType'] = imageType if expTime > 0 else "bias"
        phuInfo['expTime'] = expTime    # the header value is wrong

        return phuInfo, infoList
    
    def translate_detector(self, md):
        return 0                        # we can't use config.parse.defaults as it only handles strings

    def translate_visit(self, md):
        """Generate a unique visit from the timestamp.

        It might be better to use the 1000*runNo + seqNo, but the latter isn't currently set

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        visit_num : `int`
            Visit number, as translated
        """
        mjd = md.get("MJD-OBS")
        mmjd = mjd - 58300              # relative to 2018-07-01, just to make the visits a tiny bit smaller
        return int(1e5*mmjd)            # 86400s per day, so we need this resolution

    def translate_wavelength(self, md):
        """Translate wavelength provided by auxtel readout.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        wavelength : `int`
            The recorded wavelength as an int
        """
        return -666

    def translate_filter(self, md):
        """Translate the two filter wheels into one filter string

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        filter name : `str`
            The names of the two filters separated by a "|"; if both are empty return None
        """
        filters = []
        for k in ["FILTER1", "FILTER2"]:
            if md.exists(k):
                filters.append(md.get(k))
                            
        filterName = "|".join(filters)

        if filterName == "":
            filterName = "NONE"

        return filterName

    def translate_kid(self, md):
        """Return the end of the timestamp; the start is the day

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        the "Kirk ID" (kid) : `int`
            An identifier valid within a day
        """

        f = md.get("FILENAME")
        basename = os.path.splitext(os.path.split(f)[1])[0] # e.g. ats_exp_5_20180721023513

        tstamp = basename.split('_')[-1] # 20180721023513
        kid = tstamp[-6:]                # 023513
        kid = re.sub(r'^0+', '', kid)    # 23515

        return kid

        
    
