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
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#
"""The LsstCam Mapper."""  # necessary to suppress D100 flake8 warning.

import os
import re
import lsst.log
import lsst.geom
import lsst.utils as utils
import lsst.afw.image.utils as afwImageUtils
import lsst.afw.image as afwImage
from lsst.afw.fits import readMetadata
from lsst.obs.base import CameraMapper, MakeRawVisitInfoViaObsInfo
import lsst.obs.base.yamlCamera as yamlCamera
import lsst.daf.persistence as dafPersist
from .translators import LsstCamTranslator
from astro_metadata_translator import fix_header

from .filters import getFilterDefinitions
from .assembly import attachRawWcsFromBoresight, fixAmpGeometry, assembleUntrimmedCcd

__all__ = ["LsstCamMapper", "LsstCamMakeRawVisitInfo"]


class LsstCamMakeRawVisitInfo(MakeRawVisitInfoViaObsInfo):
    """Make a VisitInfo from the FITS header of a raw image."""


class LsstCamRawVisitInfo(LsstCamMakeRawVisitInfo):
    metadataTranslator = LsstCamTranslator


def assemble_raw(dataId, componentInfo, cls):
    """Called by the butler to construct the composite type "raw".

    Note that we still need to define "_raw" and copy various fields over.

    Parameters
    ----------
    dataId : `lsst.daf.persistence.dataId.DataId`
        The data ID.
    componentInfo : `dict`
        dict containing the components, as defined by the composite definition
        in the mapper policy.
    cls : 'object'
        Unused.

    Returns
    -------
    exposure : `lsst.afw.image.Exposure`
        The assembled exposure.
    """

    ampExps = componentInfo['raw_amp'].obj
    if len(ampExps) == 0:
        raise RuntimeError("Unable to read raw_amps for %s" % dataId)

    ccd = ampExps[0].getDetector()      # the same (full, CCD-level) Detector is attached to all ampExps
    #
    # Check that the geometry in the metadata matches cameraGeom
    #
    logger = lsst.log.Log.getLogger("LsstCamMapper")
    warned = False

    def logCmd(s, *args):
        nonlocal warned
        if warned:
            logger.debug("{}: {}".format(dataId, s), *args)
        else:
            logger.warn("{}: {}".format(dataId, s), *args)
            warned = True

    for amp, ampExp in zip(ccd, ampExps):
        fixAmpGeometry(amp, bbox=ampExp.getBBox(), metadata=ampExp.getMetadata(), logCmd=logCmd)

    exposure = assembleUntrimmedCcd(ccd, ampExps)

    md = componentInfo['raw_hdu'].obj
    fix_header(md)  # No mapper so cannot specify the translator class
    exposure.setMetadata(md)

    if not attachRawWcsFromBoresight(exposure):
        logger.warn("Unable to set WCS for %s from header as RA/Dec/Angle are unavailable" %
                    (dataId,))

    return exposure


class LsstCamBaseMapper(CameraMapper):
    """The Base Mapper for all LSST-style instruments.
    """

    packageName = 'obs_lsst'
    _cameraName = "lsstCam"
    yamlFileList = ("lsstCamMapper.yaml",)  # list of yaml files to load, keeping the first occurrence
    #
    # do not set MakeRawVisitInfoClass or translatorClass to anything other
    # than None!
    #
    # assemble_raw relies on autodetect as in butler Gen2 it doesn't know
    # its mapper and cannot use mapper.makeRawVisitInfo()
    #
    MakeRawVisitInfoClass = None
    translatorClass = None

    def __init__(self, inputPolicy=None, **kwargs):
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

        LsstCamMapper._nbit_tract = 16
        LsstCamMapper._nbit_patch = 5
        LsstCamMapper._nbit_filter = 6

        LsstCamMapper._nbit_id = 64 - (LsstCamMapper._nbit_tract + 2*LsstCamMapper._nbit_patch +
                                       LsstCamMapper._nbit_filter)

        if len(afwImage.Filter.getNames()) >= 2**LsstCamMapper._nbit_filter:
            raise RuntimeError("You have more filters defined than fit into the %d bits allocated" %
                               LsstCamMapper._nbit_filter)

    @classmethod
    def getCameraName(cls):
        return cls._cameraName

    @classmethod
    def _makeCamera(cls, policy=None, repositoryDir=None, cameraYamlFile=None):
        """Make a camera  describing the camera geometry.

        policy : ignored
        repositoryDir : ignored
        cameraYamlFile : `str`
           The full path to a yaml file to be passed to `yamlCamera.makeCamera`

        Returns
        -------
        camera : `lsst.afw.cameraGeom.Camera`
            Camera geometry.
        """

        if not cameraYamlFile:
            cameraYamlFile = os.path.join(utils.getPackageDir(cls.packageName), "policy",
                                          ("%s.yaml" % cls.getCameraName()))

        return yamlCamera.makeCamera(cameraYamlFile)

    @classmethod
    def defineFilters(cls):
        afwImageUtils.resetFilters()
        for filterDef in getFilterDefinitions():
            filterDef.declare()

    def _getRegistryValue(self, dataId, k):
        """Return a value from a dataId, or look it up in the registry if it
        isn't present."""
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
        if "channel" in dataId:    # they specified a channel
            dataId = dataId.copy()
            del dataId["channel"]  # Do not include in query
        raftName = self._getRegistryValue(dataId, "raftName")
        detectorName = self._getRegistryValue(dataId, "detectorName")

        return "%s_%s" % (raftName, detectorName)

    def _computeCcdExposureId(self, dataId):
        """Compute the 64-bit (long) identifier for a CCD exposure.

        Parameters
        ----------
        dataId : `dict`
            Data identifier including dayObs and seqNum.

        Returns
        -------
        id : `int`
            Integer identifier for a CCD exposure.
        """
        try:
            visit = self._getRegistryValue(dataId, "visit")
        except Exception:
            raise KeyError(f"Require a visit ID to calculate detector exposure ID. Got: {dataId}")

        if "detector" in dataId:
            detector = dataId["detector"]
        else:
            detector = self.translatorClass.compute_detector_num_from_name(dataId['raftName'],
                                                                           dataId['detectorName'])

        return self.translatorClass.compute_detector_exposure_id(visit, detector)

    def bypass_ccdExposureId(self, datasetType, pythonType, location, dataId):
        return self._computeCcdExposureId(dataId)

    def bypass_ccdExposureId_bits(self, datasetType, pythonType, location, dataId):
        """How many bits are required for the maximum exposure ID"""
        return 51  # max detector_exposure_id ~ 2050121299999250

    def _computeCoaddExposureId(self, dataId, singleFilter):
        """Compute the 64-bit (long) identifier for a coadd.

        Parameters
        ----------
        dataId : `dict`
            Data identifier with tract and patch.
        singleFilter : `bool`
            True means the desired ID is for a single-filter coadd, in which
            case ``dataId`` must contain filter.
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
        """The number of bits used up for patch ID bits."""
        return 64 - LsstCamMapper._nbit_id

    def bypass_deepCoaddId(self, datasetType, pythonType, location, dataId):
        return self._computeCoaddExposureId(dataId, True)

    def bypass_dcrCoaddId_bits(self, datasetType, pythonType, location, dataId):
        return self.bypass_deepCoaddId_bits(datasetType, pythonType, location, dataId)

    def bypass_dcrCoaddId(self, datasetType, pythonType, location, dataId):
        return self.bypass_deepCoaddId(datasetType, pythonType, location, dataId)

    def bypass_deepMergedCoaddId_bits(self, *args, **kwargs):
        """The number of bits used up for patch ID bits."""
        return 64 - LsstCamMapper._nbit_id

    def bypass_deepMergedCoaddId(self, datasetType, pythonType, location, dataId):
        return self._computeCoaddExposureId(dataId, False)

    def bypass_dcrMergedCoaddId_bits(self, *args, **kwargs):
        """The number of bits used up for patch ID bits."""
        return self.bypass_deepMergedCoaddId_bits(*args, **kwargs)

    def bypass_dcrMergedCoaddId(self, datasetType, pythonType, location, dataId):
        return self.bypass_deepMergedCoaddId(datasetType, pythonType, location, dataId)

    def query_raw_amp(self, format, dataId):
        """Return a list of tuples of values of the fields specified in
        format, in order.

        Parameters
        ----------
        format : `list`
            The desired set of keys.
        dataId : `dict`
            A possible-incomplete ``dataId``.

        Returns
        -------
        fields : `list` of `tuple`
            Values of the fields specified in ``format``.

        Raises
        ------
        ValueError
            The channel number requested in ``dataId`` is out of range.
        """
        nChannel = 16                   # number of possible channels, 1..nChannel

        if "channel" in dataId:         # they specified a channel
            dataId = dataId.copy()
            channel = dataId.pop('channel')  # Do not include in query below
            if channel > nChannel or channel < 1:
                raise ValueError(f"Requested channel is out of range 0 < {channel} <= {nChannel}")
            channels = [channel]
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
    # The composite type "raw" doesn't provide e.g. query_raw, so we defined
    # type _raw in the .paf file with the same template, and forward requests
    # as necessary
    #

    def query_raw(self, *args, **kwargs):
        """Magic method that is called automatically if it exists.

        This code redirects the call to the right place, necessary because of
        leading underscore on ``_raw``.
        """
        return self.query__raw(*args, **kwargs)

    def map_raw_md(self, *args, **kwargs):
        """Magic method that is called automatically if it exists.

        This code redirects the call to the right place, necessary because of
        leading underscore on ``_raw``.
        """
        return self.map__raw_md(*args, **kwargs)

    def map_raw_filename(self, *args, **kwargs):
        """Magic method that is called automatically if it exists.

        This code redirects the call to the right place, necessary because of
        leading underscore on ``_raw``.
        """
        return self.map__raw_filename(*args, **kwargs)

    def bypass_raw_filename(self, *args, **kwargs):
        """Magic method that is called automatically if it exists.

        This code redirects the call to the right place, necessary because of
        leading underscore on ``_raw``.
        """
        return self.bypass__raw_filename(*args, **kwargs)

    def map_raw_visitInfo(self, *args, **kwargs):
        """Magic method that is called automatically if it exists.

        This code redirects the call to the right place, necessary because of
        leading underscore on ``_raw``.
        """
        return self.map__raw_visitInfo(*args, **kwargs)

    def bypass_raw_visitInfo(self, datasetType, pythonType, location, dataId):
        fileName = location.getLocationsWithRoot()[0]
        mat = re.search(r"\[(\d+)\]$", fileName)
        if mat:
            hdu = int(mat.group(1))
            md = readMetadata(fileName, hdu=hdu)
        else:
            md = readMetadata(fileName)  # or hdu = INT_MIN; -(1 << 31)

        makeVisitInfo = self.MakeRawVisitInfoClass(log=self.log)
        fix_header(md, translator_class=self.translatorClass)
        return makeVisitInfo(md)

    def std_raw_amp(self, item, dataId):
        return self._standardizeExposure(self.exposures['raw_amp'], item, dataId,
                                         trimmed=False, setVisitInfo=False)

    def std_raw(self, item, dataId, filter=True):
        """Standardize a raw dataset by converting it to an
        `~lsst.afw.image.Exposure` instead of an `~lsst.afw.image.Image`."""

        return self._standardizeExposure(self.exposures['raw'], item, dataId, trimmed=False,
                                         setVisitInfo=False,  # it's already set, and the metadata's stripped
                                         filter=filter)


class LsstCamMapper(LsstCamBaseMapper):
    """The mapper for lsstCam."""
    translatorClass = LsstCamTranslator
    MakeRawVisitInfoClass = LsstCamRawVisitInfo
    _cameraName = "lsstCam"
