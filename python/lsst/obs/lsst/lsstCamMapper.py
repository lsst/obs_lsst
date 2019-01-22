#
# LSST Data Management System
# Copyright 2016 LSST Corporation.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
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
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#
"""The LsstCam Mapper."""  # necessary to suppress D100 flake8 warning.

import os
import re
import lsst.log
import lsst.afw.image.utils as afwImageUtils
import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage
from lsst.afw.fits import readMetadata
from lsst.obs.base import CameraMapper, MakeRawVisitInfoViaObsInfo, bboxFromIraf
import lsst.daf.persistence as dafPersist

from . import lsstCam

__all__ = ["LsstCamMapper"]


class LsstCamMakeRawVisitInfo(MakeRawVisitInfoViaObsInfo):
    """Make a VisitInfo from the FITS header of a raw image."""


def assemble_raw(dataId, componentInfo, cls):
    """Called by the butler to construct the composite type "raw".

    Note that we still need to define "_raw" and copy various fields over.

    Parameters
    ----------
    dataId : `lsst.daf.persistence.dataId.DataId`
        the data ID
    componentInfo : `dict`
        dict containing the components, as defined by the composite definition in the mapper policy
    cls : 'object'
        unused

    Returns
    -------
    exposure : `lsst.afw.image.exposure.exposure`
        The assembled exposure
    """
    from lsst.ip.isr import AssembleCcdTask

    config = AssembleCcdTask.ConfigClass()
    config.doTrim = False

    assembleTask = AssembleCcdTask(config=config)

    ampExps = componentInfo['raw_amp'].obj
    if len(ampExps) == 0:
        raise RuntimeError("Unable to read raw_amps for %s" % dataId)

    ccd = ampExps[0].getDetector()      # the same (full, CCD-level) Detector is attached to all ampExps
    #
    # Check that the geometry in the metadata matches cameraGeom
    #
    logger = lsst.log.Log.getLogger("LsstCamMapper")
    warned = False
    for i, (amp, ampExp) in enumerate(zip(ccd, ampExps)):
        ampMd = ampExp.getMetadata().toDict()

        if amp.getRawBBox() != ampExp.getBBox():  # Oh dear. cameraGeom is wrong -- probably overscan
            if amp.getRawDataBBox().getDimensions() != amp.getBBox().getDimensions():
                raise RuntimeError("Active area is the wrong size: %s v. %s" %
                                   (amp.getRawDataBBox().getDimensions(), amp.getBBox().getDimensions()))
            if not warned:
                logger.warn("amp.getRawBBox() != data.getBBox(); patching. (%s v. %s)",
                            amp.getRawBBox(), ampExp.getBBox())
                warned = True

            w,  h  = ampExp.getBBox().getDimensions()  # noqa E221, E241
            ow, oh = amp.getRawBBox().getDimensions()  # "old" (cameraGeom) dimensions
            #
            # We could trust the BIASSEC keyword, or we can just assume that they've changed
            # the number of overscan pixels (serial and/or parallel).  As Jim Chiang points out,
            # the latter is safer
            #
            bbox = amp.getRawHorizontalOverscanBBox()
            hOverscanBBox = afwGeom.BoxI(bbox.getBegin(),
                                         afwGeom.ExtentI(w - bbox.getBeginX(), bbox.getHeight()))
            bbox = amp.getRawVerticalOverscanBBox()
            vOverscanBBox = afwGeom.BoxI(bbox.getBegin(),
                                         afwGeom.ExtentI(bbox.getWidth(), h - bbox.getBeginY()))

            amp.setRawBBox(ampExp.getBBox())
            amp.setRawHorizontalOverscanBBox(hOverscanBBox)
            amp.setRawVerticalOverscanBBox(vOverscanBBox)
            #
            # This gets all the geometry right for the amplifier, but the size of the untrimmed image
            # will be wrong and we'll put the amp sections in the wrong places, i.e.
            #   amp.getRawXYOffset()
            # will be wrong.  So we need to recalculate the offsets.
            #
            xRawExtent, yRawExtent = amp.getRawBBox().getDimensions()

            x0, y0 = amp.getRawXYOffset()
            ix, iy = x0//ow, y0/oh
            x0, y0 = ix*xRawExtent, iy*yRawExtent
            amp.setRawXYOffset(afwGeom.ExtentI(ix*xRawExtent, iy*yRawExtent))
        #
        # Check the "IRAF" keywords, but don't abort if they're wrong
        #
        # Only warn about the first amp, use debug for the others
        #
        detsec = bboxFromIraf(ampMd["DETSEC"]) if "DETSEC" in ampMd else None
        datasec = bboxFromIraf(ampMd["DATASEC"]) if "DATASEC" in ampMd else None
        biassec = bboxFromIraf(ampMd["BIASSEC"]) if "BIASSEC" in ampMd else None

        logCmd = logger.warn if i == 0 else logger.debug
        if detsec and amp.getBBox() != detsec:
            logCmd("DETSEC doesn't match for %s (%s != %s)", dataId, amp.getBBox(), detsec)
        if datasec and amp.getRawDataBBox() != datasec:
            logCmd("DATASEC doesn't match for %s (%s != %s)", dataId, amp.getRawDataBBox(), detsec)
        if biassec and amp.getRawHorizontalOverscanBBox() != biassec:
            logCmd("BIASSEC doesn't match for %s (%s != %s)",
                   dataId, amp.getRawHorizontalOverscanBBox(), detsec)

    ampDict = {}
    for amp, ampExp in zip(ccd, ampExps):
        ampDict[amp.getName()] = ampExp

    exposure = assembleTask.assembleCcd(ampDict)

    md = componentInfo['raw_hdu'].obj
    exposure.setMetadata(md)
    #
    # We need to standardize, but have no legal way to call std_raw.  The butler should do this for us.
    #
    global _camera, _lsstCamMapper      # Dangerous file-level cache set by Mapper.__initialiseCache()

    try:
        exposure = _lsstCamMapper.std_raw(exposure, dataId)
    except Exception:
        exposure = _lsstCamMapper.std_raw(exposure, dataId, filter=False)

    setWcsFromBoresight = True          # Construct the initial WCS from the boresight/rotation?
    if setWcsFromBoresight:
        visitInfo = exposure.getInfo().getVisitInfo()
        boresight = visitInfo.getBoresightRaDec()
        rotangle = visitInfo.getBoresightRotAngle()

        if boresight.isFinite():
            exposure.setWcs(getWcsFromDetector(_camera, exposure.getDetector(), boresight,
                                               90*afwGeom.degrees - rotangle))
        else:
            # Should only warn for science observations but VisitInfo does not know
            logger.warn("Unable to set WCS for %s from header as RA/Dec/Angle are unavailable" %
                        (dataId,))

    return exposure

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
# This code will be replaced by functionality in afw;  DM-14932 (done), DM-14980
#
import lsst.afw.cameraGeom as cameraGeom # noqa F811


def getWcsFromDetector(camera, detector, boresight, rotation=0*afwGeom.degrees, flipX=False):
    """Given a camera, detector and (boresight, rotation), return that detector's WCS

        Parameters
        ----------
        camera: `lsst.afw.cameraGeom.Camera`  The camera containing the detector
        detector: `lsst.afw.cameraGeom.Detector`  A detector in a camera
        boresight: `lsst.afw.geom.SpherePoint`  The boresight of the observation
        rotation: `lsst.afw.geom.Angle` The rotation angle of the camera

    The rotation is "rotskypos", the angle of sky relative to camera coordinates
    (from North over East)
    """
    trans = camera.getTransform(detector.makeCameraSys(cameraGeom.PIXELS),
                                detector.makeCameraSys(cameraGeom.FIELD_ANGLE))

    wcs = afwGeom.makeSkyWcs(trans, rotation, flipX, boresight)

    return wcs

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-


class LsstCamMapper(CameraMapper):
    """The Mapper for LsstCam."""

    packageName = 'obs_lsst'
    MakeRawVisitInfoClass = LsstCamMakeRawVisitInfo
    yamlFileList = ("lsstCamMapper.yaml",)  # list of yaml files to load, keeping the first occurrence

    def __initialiseCache(self):
        """Initialise file-level cache.

        We do this because it's expensive to build Cameras and Mappers, but it is not a good idea in the
        medium or long run!
        """
        global _camera, _lsstCamMapper

        try:
            _camera
        except NameError:
            _camera = self._makeCamera(None, None)
            _lsstCamMapper = self

    @classmethod
    def __clearCache(cls):
        """Clear file-level cache.
        """

        try:
            del globals()['_camera']
        except KeyError:
            pass

        try:
            del globals()['_lsstCamMapper']
        except KeyError:
            pass

    def __init__(self, inputPolicy=None, **kwargs):
        """Initialization for the LsstCam Mapper."""
        #
        # Merge the list of .yaml files
        #
        policy = None
        for yamlFile in self.yamlFileList:
            policyFile = dafPersist.Policy.defaultPolicyFile(self.packageName, yamlFile, "policy")
            npolicy = dafPersist.Policy(policyFile)

            if policy is None:
                policy = npolicy
            else:
                policy.merge(npolicy)
        #
        # Look for the calibrations root "root/CALIB" if not supplied
        #
        if kwargs.get('root', None) and not kwargs.get('calibRoot', None):
            calibSearch = [os.path.join(kwargs['root'], 'CALIB')]
            if "repositoryCfg" in kwargs:
                calibSearch += [os.path.join(cfg.root, 'CALIB') for cfg in kwargs["repositoryCfg"].parents if
                                hasattr(cfg, "root")]
                calibSearch += [cfg.root for cfg in kwargs["repositoryCfg"].parents if hasattr(cfg, "root")]
            for calibRoot in calibSearch:
                if os.path.exists(os.path.join(calibRoot, "calibRegistry.sqlite3")):
                    kwargs['calibRoot'] = calibRoot
                    break
            if not kwargs.get('calibRoot', None):
                lsst.log.Log.getLogger("LsstCamMapper").warn("Unable to find valid calib root directory")

        super().__init__(policy, os.path.dirname(policyFile), **kwargs)
        #
        # The composite objects don't seem to set these
        #
        for d in (self.mappings, self.exposures):
            d['raw'] = d['_raw']

        self.defineFilters()

        self.__initialiseCache()

        LsstCamMapper._nbit_tract = 16
        LsstCamMapper._nbit_patch = 5
        LsstCamMapper._nbit_filter = 6

        LsstCamMapper._nbit_id = 64 - (LsstCamMapper._nbit_tract + 2*LsstCamMapper._nbit_patch +
                                       LsstCamMapper._nbit_filter)

        if len(afwImage.Filter.getNames()) >= 2**LsstCamMapper._nbit_filter:
            raise RuntimeError("You have more filters defined than fit into the %d bits allocated" %
                               LsstCamMapper._nbit_filter)

    @classmethod
    def defineFilters(cls):
        # The order of these defineFilter commands matters as their IDs are used to generate at least some
        # object IDs (e.g. on coadds) and changing the order will invalidate old objIDs
        afwImageUtils.resetFilters()
        afwImageUtils.defineFilter('NONE', 0.0, alias=['no_filter', "OPEN"])
        afwImageUtils.defineFilter('275CutOn', 0.0, alias=[])
        afwImageUtils.defineFilter('550CutOn', 0.0, alias=[])
        # The LSST Filters from L. Jones 04/07/10
        afwImageUtils.defineFilter('u', lambdaEff=364.59, lambdaMin=324.0, lambdaMax=395.0)
        afwImageUtils.defineFilter('g', lambdaEff=476.31, lambdaMin=405.0, lambdaMax=552.0)
        afwImageUtils.defineFilter('r', lambdaEff=619.42, lambdaMin=552.0, lambdaMax=691.0)
        afwImageUtils.defineFilter('i', lambdaEff=752.06, lambdaMin=818.0, lambdaMax=921.0)
        afwImageUtils.defineFilter('z', lambdaEff=866.85, lambdaMin=922.0, lambdaMax=997.0)
        # official y filter
        afwImageUtils.defineFilter('y', lambdaEff=971.68, lambdaMin=975.0, lambdaMax=1075.0, alias=['y4'])

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing the camera geometry."""
        return lsstCam.LsstCam()

    def _getRegistryValue(self, dataId, k):
        """Return a value from a dataId, or look it up in the registry if it isn't present"""
        if k in dataId:
            return dataId[k]
        else:
            dataType = "bias" if "taiObs" in dataId else "raw"

            try:
                return self.queryMetadata(dataType, [k], dataId)[0][0]
            except IndexError:
                raise RuntimeError("Unable to lookup %s in \"%s\" registry for dataId %s" %
                                   (k, dataType, dataId))

    def _extractDetectorName(self, dataId):
        raftName = self._getRegistryValue(dataId, "raftName")
        detectorName = self._getRegistryValue(dataId, "detectorName")

        return "%s_%s" % (raftName, detectorName)

    def _computeCcdExposureId(self, dataId):
        """Compute the 64-bit (long) identifier for a CCD exposure.

        @param dataId (dict) Data identifier including visit and detector
        """
        visit = dataId['visit']

        if "detector" in dataId:
            detector = dataId["detector"]
        else:
            camera = self.camera
            fullName = self._extractDetectorName(dataId)
            detector = camera[fullName].getId()

        return 200*visit + detector

    def bypass_ccdExposureId(self, datasetType, pythonType, location, dataId):
        return self._computeCcdExposureId(dataId)

    def bypass_ccdExposureId_bits(self, datasetType, pythonType, location, dataId):
        """How many bits are required for the maximum exposure ID"""
        return 32  # just a guess, but this leaves plenty of space for sources

    def _computeCoaddExposureId(self, dataId, singleFilter):
        """Compute the 64-bit (long) identifier for a coadd.
        @param dataId (dict)       Data identifier with tract and patch.
        @param singleFilter (bool) True means the desired ID is for a single-
                                   filter coadd, in which case dataId
                                   must contain filter.
        """

        tract = int(dataId['tract'])
        if tract < 0 or tract >= 2**LsstCamMapper._nbit_tract:
            raise RuntimeError('tract not in range [0,%d)' % (2**LsstCamMapper._nbit_tract))
        patchX, patchY = [int(patch) for patch in dataId['patch'].split(',')]
        for p in (patchX, patchY):
            if p < 0 or p >= 2**LsstCamMapper._nbit_patch:
                raise RuntimeError('patch component not in range [0, %d)' % 2**LsstCamMapper._nbit_patch)
        oid = (((tract << LsstCamMapper._nbit_patch) + patchX) << LsstCamMapper._nbit_patch) + patchY
        if singleFilter:
            return (oid << LsstCamMapper._nbit_filter) + afwImage.Filter(dataId['filter']).getId()
        return oid

    def bypass_deepCoaddId_bits(self, *args, **kwargs):
        """The number of bits used up for patch ID bits"""
        return 64 - LsstCamMapper._nbit_id

    def bypass_deepCoaddId(self, datasetType, pythonType, location, dataId):
        return self._computeCoaddExposureId(dataId, True)

    def bypass_dcrCoaddId_bits(self, datasetType, pythonType, location, dataId):
        return self.bypass_deepCoaddId_bits(datasetType, pythonType, location, dataId)

    def bypass_dcrCoaddId(self, datasetType, pythonType, location, dataId):
        return self.bypass_deepCoaddId(datasetType, pythonType, location, dataId)

    def bypass_deepMergedCoaddId_bits(self, *args, **kwargs):
        """The number of bits used up for patch ID bits"""
        return 64 - LsstCamMapper._nbit_id

    def bypass_deepMergedCoaddId(self, datasetType, pythonType, location, dataId):
        return self._computeCoaddExposureId(dataId, False)

    def bypass_dcrMergedCoaddId_bits(self, *args, **kwargs):
        """The number of bits used up for patch ID bits"""
        return self.bypass_deepMergedCoaddId_bits(*args, **kwargs)

    def bypass_dcrMergedCoaddId(self, datasetType, pythonType, location, dataId):
        return self.bypass_deepMergedCoaddId(datasetType, pythonType, location, dataId)

    def query_raw_amp(self, format, dataId):
        """!Return a list of tuples of values of the fields specified in format, in order.

        @param format  The desired set of keys
        @param dataId  A possible-incomplete dataId
        """
        nChannel = 16                   # number of possible channels, 1..nChannel

        if "channel" in dataId:         # they specified a channel
            dataId = dataId.copy()
            channels = [dataId.pop('channel')]
        else:
            channels = range(1, nChannel + 1)  # we want all possible channels

        if "channel" in format:           # they asked for a channel, but we mustn't query for it
            format = list(format)
            channelIndex = format.index('channel')  # where channel values should go
            format.pop(channelIndex)
        else:
            channelIndex = None

        dids = []                       # returned list of dataIds
        for value in self.query_raw(format, dataId):
            if channelIndex is None:
                dids.append(value)
            else:
                for c in channels:
                    did = list(value)
                    did.insert(channelIndex, c)
                    dids.append(tuple(did))

        return dids
    #
    # The composite type "raw" doesn't provide e.g. query_raw, so we defined type _raw in the .paf file
    # with the same template, and forward requests as necessary
    #

    def query_raw(self, *args, **kwargs):
        """Magic method that is called automatically if it exists.

        This code redirects the call to the right place, necessary because of leading underscore on _raw.
        """
        return self.query__raw(*args, **kwargs)

    def map_raw_md(self, *args, **kwargs):
        """Magic method that is called automatically if it exists.

        This code redirects the call to the right place, necessary because of leading underscore on _raw.
        """
        return self.map__raw_md(*args, **kwargs)

    def map_raw_filename(self, *args, **kwargs):
        """Magic method that is called automatically if it exists.

        This code redirects the call to the right place, necessary because of leading underscore on _raw.
        """
        return self.map__raw_filename(*args, **kwargs)

    def bypass_raw_filename(self, *args, **kwargs):
        """Magic method that is called automatically if it exists.

        This code redirects the call to the right place, necessary because of leading underscore on _raw.
        """
        return self.bypass__raw_filename(*args, **kwargs)

    def map_raw_visitInfo(self, *args, **kwargs):
        """Magic method that is called automatically if it exists.

        This code redirects the call to the right place, necessary because of leading underscore on _raw.
        """
        return self.map__raw_visitInfo(*args, **kwargs)

    def bypass_raw_visitInfo(self, datasetType, pythonType, location, dataId):
        if False:
            # lsst.afw.fits.readMetadata() doesn't honour [hdu] suffixes in filenames
            #
            # We could workaround this by moving the "else" block into obs_base,
            # or by changing afw
            #
            return self.bypass__raw_visitInfo(datasetType, pythonType, location, dataId)
        else:
            fileName = location.getLocationsWithRoot()[0]
            mat = re.search(r"\[(\d+)\]$", fileName)
            if mat:
                hdu = int(mat.group(1))
                md = readMetadata(fileName, hdu=hdu)
            else:
                md = readMetadata(fileName)  # or hdu = INT_MIN; -(1 << 31)

            return afwImage.VisitInfo(md)

    def std_raw_amp(self, item, dataId):
        return self._standardizeExposure(self.exposures['raw_amp'], item, dataId,
                                         trimmed=False, setVisitInfo=False)

    def std_raw(self, item, dataId, filter=True):
        """Standardize a raw dataset by converting it to an Exposure instead of an Image"""
        return self._standardizeExposure(self.exposures['raw'], item, dataId,
                                         trimmed=False, setVisitInfo=True, filter=filter)
