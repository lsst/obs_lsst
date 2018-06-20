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

import lsst.afw.image.utils as afwImageUtils
import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage
from lsst.afw.fits import readMetadata
from lsst.obs.base import CameraMapper, MakeRawVisitInfo
import lsst.daf.persistence as dafPersist

from lsst.obs.lsstCam import LsstCam

__all__ = ["LsstCamMapper"]


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

    ampDict = {}
    for amp, ampExp in zip(ccd, ampExps):
        ampDict[amp.getName()] = ampExp

    exposure = assembleTask.assembleCcd(ampDict)

    md = componentInfo['raw_hdu'].obj
    exposure.setMetadata(md)
    #
    # We need to standardize, but have no legal way to call std_raw.  The butler should do this for us.
    #
    ccm = LsstCamMapper()
    exposure = ccm.std_raw(exposure, dataId)

    return exposure


class LsstCamMapper(CameraMapper):
    """The Mapper for LsstCam."""

    packageName = 'obs_lsstCam'
    MakeRawVisitInfoClass = LsstCamMakeRawVisitInfo

    def __init__(self, inputPolicy=None, **kwargs):
        """Initialization for the LsstCam Mapper."""
        policyFile = dafPersist.Policy.defaultPolicyFile(self.packageName, "lsstCamMapper.yaml", "policy")
        policy = dafPersist.Policy(policyFile)

        CameraMapper.__init__(self, policy, os.path.dirname(policyFile), **kwargs)
        #
        # The composite objects don't seem to set these
        #
        for d in (self.mappings, self.exposures):
            d['raw'] = d['_raw']

        # self.filterIdMap = {}           # where is this used?  Generating objIds??

        afwImageUtils.defineFilter('NONE', 0.0, alias=['no_filter', "OPEN"])
        afwImageUtils.defineFilter('275CutOn', 0.0, alias=[])
        afwImageUtils.defineFilter('550CutOn', 0.0, alias=[])

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing the camera geometry."""
        return LsstCam()

    def _extractDetectorName(self, dataId):
        return dataId["ccd"]

    def _computeCcdExposureId(self, dataId):
        """Compute the 64-bit (long) identifier for a CCD exposure.

        @param dataId (dict) Data identifier with visit
        """
        visit = dataId['visit']
        return int(visit)

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

    def X_validate(self, dataId):
        """Method has X_ prepended and thus not currently live."""
        visit = dataId.get("visit")
        if visit is not None and not isinstance(visit, int):
            dataId["visit"] = int(visit)
        return dataId

    def X__setCcdExposureId(self, propertyList, dataId):
        """Method has X_ prepended and thus not currently live."""
        propertyList.set("Computed_ccdExposureId", self._computeCcdExposureId(dataId))
        return propertyList

    def X_bypass_defects(self, datasetType, pythonType, location, dataId):
        """Method has X_ prepended and thus not currently live.

        Since we have no defects, return an empty list. Fix this when defects exist.
        """
        return [afwImage.DefectBase(afwGeom.Box2I(afwGeom.Point2I(x0, y0), afwGeom.Point2I(x1, y1))) for
                x0, y0, x1, y1 in (
                    # These may be hot pixels, but we'll treat them as bad until we can get more data
                    (3801, 666, 3805, 669),
                    (3934, 582, 3936, 589),
        )]

    def X__defectLookup(self, dataId):
        """Method has X_ prepended and thus not currently live.

        Also, method is hacky method and should not exist.
        This function needs to return a non-None value otherwise the mapper gives up
        on trying to find the defects.  I wanted to be able to return a list of defects constructed
        in code rather than reconstituted from persisted files, so I return a dummy value.
        """
        return "this_is_a_hack"

    def X_standardizeCalib(self, dataset, item, dataId):
        """Standardize a calibration image read in by the butler.

        Some calibrations are stored on disk as Images instead of MaskedImages
        or Exposures.  Here, we convert it to an Exposure.

        @param dataset  Dataset type (e.g., "bias", "dark" or "flat")
        @param item  The item read by the butler
        @param dataId  The data identifier (unused, included for future flexibility)
        @return standardized Exposure
        """
        mapping = self.calibrations[dataset]
        if "MaskedImage" in mapping.python:
            exp = afwImage.makeExposure(item)
        elif "Image" in mapping.python:
            if hasattr(item, "getImage"):  # For DecoratedImageX
                item = item.getImage()
                exp = afwImage.makeExposure(afwImage.makeMaskedImage(item))
        elif "Exposure" in mapping.python:
            exp = item
        else:
            raise RuntimeError("Unrecognised python type: %s" % mapping.python)

        parent = super(CameraMapper, self)
        if hasattr(parent, "std_" + dataset):
            return getattr(parent, "std_" + dataset)(exp, dataId)
        return self._standardizeExposure(mapping, exp, dataId)

    def X_std_bias(self, item, dataId):
        """Method has X_ prepended and thus not currently live."""
        return self.standardizeCalib("bias", item, dataId)

    def X_std_dark(self, item, dataId):
        """Method has X_ prepended and thus not currently live."""
        exp = self.standardizeCalib("dark", item, dataId)
        # exp.getCalib().setExptime(1.0)
        return exp

    def X_std_flat(self, item, dataId):
        """Method has X_ prepended and thus not currently live."""
        return self.standardizeCalib("flat", item, dataId)

    def X_std_fringe(self, item, dataId):
        """Method has X_ prepended and thus not currently live."""
        return self.standardizeCalib("flat", item, dataId)
