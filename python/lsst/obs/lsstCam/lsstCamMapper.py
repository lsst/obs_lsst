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

from __future__ import division, print_function

import os

import lsst.log
import lsst.pex.exceptions as pexExcept
import lsst.afw.image.utils as afwImageUtils
import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage
from lsst.afw.fits import readMetadata
from lsst.obs.base import CameraMapper, MakeRawVisitInfo, bboxFromIraf
import lsst.daf.persistence as dafPersist

from . import lsstCam

__all__ = ["LsstCamMapper", "ImsimMapper", "PhosimMapper"]


class LsstCamMakeRawVisitInfo(MakeRawVisitInfo):
    """functor to make a VisitInfo from the FITS header of a raw image."""

    def setArgDict(self, md, argDict):
        """Fill an argument dict with arguments for makeVisitInfo and pop associated metadata.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata
        argDict : `dict`
            The argument dictionary used to construct the visit info, modified in place
        """
        super(LsstCamMakeRawVisitInfo, self).setArgDict(md, argDict)
        argDict["darkTime"] = self.popFloat(md, "DARKTIME")

        # Done setting argDict; check values now that all the header keywords have been consumed
        argDict["darkTime"] = self.getDarkTime(argDict)

    def getDateAvg(self, md, exposureTime):
        """Return date at the middle of the exposure.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata
        exposureTime : `float`
            exposure time, measure in seconds
        """
        dateObs = self.popIsoDate(md, "DATE-OBS")
        return self.offsetDate(dateObs, 0.5*exposureTime)


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

        if amp.getRawBBox() != ampExp.getBBox(): # Oh dear. cameraGeom is wrong -- probably overscan
            if not warned:
                logger.warn("amp.getRawBBox() != data.getBBox(); patching. (%s v. %s)" %
                            (amp.getRawBBox(), ampExp.getBBox()))
                warned = True

            w,  h  = ampExp.getBBox().getDimensions()
            ow, oh = amp.getRawBBox().getDimensions() # "old" (cameraGeom) dimensions
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
            logCmd("DETSEC doesn't match for %s (%s != %s)" %
                   (dataId, amp.getBBox(), detsec))
        if datasec and amp.getRawDataBBox() != datasec:
            logCmd("DATASEC doesn't match for %s (%s != %s)" %
                        (dataId, amp.getRawDataBBox(), detsec))
        if biassec and amp.getRawHorizontalOverscanBBox() != biassec:
            logCmd("BIASSEC doesn't match for %s (%s != %s)" %
                   (dataId, amp.getRawHorizontalOverscanBBox(), detsec))

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

    exposure = _lsstCamMapper.std_raw(exposure, dataId)

    setWcsFromBoresight = True          # Construct the initial WCS from the boresight/rotation?
    if setWcsFromBoresight:
        try:
            ratel, dectel = md.getScalar("RATEL"), md.getScalar("DECTEL")
            rotangle = md.getScalar("ROTANGLE")*afwGeom.degrees
        except pexExcept.NotFoundError as e:
            ratel, dectel, rotangle = '', '', ''
            
        if ratel == '' or dectel == '' or rotangle == '': # FITS for None
            logger.warn("Unable to set WCS for %s from header as RATEL/DECTEL/ROTANGLE are unavailable" %
                        (dataId,))
        else:
            boresight = afwGeom.PointD(ratel, dectel)
            exposure.setWcs(getWcsFromDetector(_camera, exposure.getDetector(), boresight,
                                               90*afwGeom.degrees - rotangle))

    return exposure

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
# This code will be replaced by functionality in afw;  DM-14932
#
import astshim
import lsst.afw.cameraGeom as cameraGeom
import numpy as np                      # only for pi!

def getWcsFromDetector(camera, detector, boresight, rotation=0*afwGeom.degrees, flipX=False):
    """Given a camera, detector and (boresight, rotation), return that detector's WCS

        Parameters
        ----------
        camera: `lsst.afw.cameraGeom.Camera`  The camera containing the detector
        detector: `lsst.afw.cameraGeom.Detector`  A detector in a camera
        boresight: `lsst.afw.geom.Point2D`  The boresight of the observation
        rotation: `lsst.afw.geom.Angle` The rotation angle of the camera

    The rotation is "rotskypos", the angle of sky relative to camera coordinates
    (from North over East)
    """
    trans = camera.getTransform(detector.makeCameraSys(cameraGeom.PIXELS),
                                detector.makeCameraSys(cameraGeom.FIELD_ANGLE))
    polyMap = trans.getMapping()
    radToDeg = astshim.ZoomMap(2, 180/np.pi) # convert from radians to degrees
    polyMap = polyMap.then(radToDeg)

    pixelFrame = astshim.Frame(2, "Domain=PIXELS")
    iwcFrame = astshim.Frame(2, "Domain=IWC")

    frameDict = astshim.FrameDict(pixelFrame, polyMap, iwcFrame)

    crpix = afwGeom.PointD(0, 0)
    crval = afwGeom.SpherePoint(*boresight, afwGeom.degrees)
    cd = afwGeom.makeCdMatrix(1.0*afwGeom.degrees, rotation, flipX)
    iwcToSkyWcs = afwGeom.makeSkyWcs(crpix, crval, cd)

    iwcToSkyMap = iwcToSkyWcs.getFrameDict().getMapping("PIXELS", "SKY")
    skyFrame = iwcToSkyWcs.getFrameDict().getFrame("SKY")

    frameDict.addFrame("IWC", iwcToSkyMap, skyFrame)

    wcs = afwGeom.SkyWcs(frameDict)

    return wcs

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

class LsstCamMapper(CameraMapper):
    """The Mapper for LsstCam."""

    packageName = 'obs_lsstCam'
    MakeRawVisitInfoClass = LsstCamMakeRawVisitInfo
    yamlFileList = ("lsstCamMapper.yaml",) # list of yaml files to load, keeping the first occurrence

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
                lsst.log.Log.getLogger("LsstCamMapper").warn("Unable to find calib root directory")

        super(LsstCamMapper, self).__init__(policy, os.path.dirname(policyFile), **kwargs)
        #
        # The composite objects don't seem to set these
        #
        for d in (self.mappings, self.exposures):
            d['raw'] = d['_raw']

        self.defineFilters()

        self.__initialiseCache()

    @classmethod
    def defineFilters(cls):
        # The order of these defineFilter commands matters as their IDs are used to generate at least some
        # object IDs (e.g. on coadds) and changing the order will invalidate old objIDs
        afwImageUtils.resetFilters()
        afwImageUtils.defineFilter('NONE', 0.0, alias=['no_filter', "OPEN"])
        afwImageUtils.defineFilter('275CutOn', 0.0, alias=[])
        afwImageUtils.defineFilter('550CutOn', 0.0, alias=[])
        # The LSST Filters from L. Jones 04/07/10
        afwImageUtils.defineFilter('u', 364.59)
        afwImageUtils.defineFilter('g', 476.31)
        afwImageUtils.defineFilter('r', 619.42)
        afwImageUtils.defineFilter('i', 752.06)
        afwImageUtils.defineFilter('z', 866.85)
        afwImageUtils.defineFilter('y', 971.68, alias=['y4'])  # official y filter

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
            fullName = "%s_%s" % (dataId["raftName"], dataId["detectorName"])
            detector = camera._nameDetectorDict[fullName].getId()

        return 200*visit + detector

    def bypass_ccdExposureId(self, datasetType, pythonType, location, dataId):
        return self._computeCcdExposureId(dataId)

    def bypass_ccdExposureId_bits(self, datasetType, pythonType, location, dataId):
        """How many bits are required for the maximum exposure ID"""
        return 32  # just a guess, but this leaves plenty of space for sources

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
            import re
            import lsst.afw.image as afwImage

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

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
# We need a mapper class for each new distinct collection of LSST CCDs; you'll also
# need to make the obvious changes to lsstCamp.py
#
# Don't forget to add your mapper to __all__ at the top of this file
#
class ImsimMapper(LsstCamMapper):
    """The Mapper for the imsim simulations of the LsstCam."""

    @classmethod
    def getCameraName(cls):
        return "imsim"

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing the camera geometry."""
        return lsstCam.ImsimCam()

    @classmethod
    def getCameraName(cls) :
        return 'imsim'

class PhosimMapper(LsstCamMapper):
    """The Mapper for the phosim simulations of the LsstCam."""

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing the camera geometry."""
        return lsstCam.PhosimCam()

    @classmethod
    def getCameraName(cls) :
        return 'phosim'
