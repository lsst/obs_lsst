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
import os

import lsst.log
import lsst.daf.persistence as dafPersist
from lsst.obs.base import CameraMapper

from . import LsstCamMapper, LsstCamMakeRawVisitInfo
from .ingest import LsstCamParseTask
from .translators import LsstCamImSimTranslator
from ._instrument import LsstCamImSim
from .filters import LSSTCAM_IMSIM_FILTER_DEFINITIONS

__all__ = ["ImsimMapper", "ImsimParseTask"]


class ImsimMakeRawVisitInfo(LsstCamMakeRawVisitInfo):
    """Make a VisitInfo from the FITS header of a raw image."""
    metadataTranslator = LsstCamImSimTranslator


class ImsimMapper(LsstCamMapper):
    """The Mapper for the imsim simulations of the LsstCam."""
    translatorClass = LsstCamImSimTranslator
    MakeRawVisitInfoClass = ImsimMakeRawVisitInfo
    _gen3instrument = LsstCamImSim

    _cameraName = "imsim"
    yamlFileList = ["imsim/imsimMapper.yaml"] + list(LsstCamMapper.yamlFileList)
    filterDefinitions = LSSTCAM_IMSIM_FILTER_DEFINITIONS

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
        if kwargs.get("root", None) and not kwargs.get("calibRoot", None):
            calibSearch = [os.path.join(kwargs["root"], "CALIB")]
            if "repositoryCfg" in kwargs:
                calibSearch += [os.path.join(cfg.root, "CALIB") for cfg in kwargs["repositoryCfg"].parents if
                                hasattr(cfg, "root")]
                calibSearch += [cfg.root for cfg in kwargs["repositoryCfg"].parents if hasattr(cfg, "root")]
            for calibRoot in calibSearch:
                if os.path.exists(os.path.join(calibRoot, "calibRegistry.sqlite3")):
                    kwargs["calibRoot"] = calibRoot
                    break
            if not kwargs.get("calibRoot", None):
                lsst.log.Log.getLogger("LsstCamMapper").warning("Unable to find valid calib root directory")

        CameraMapper.__init__(self, policy, os.path.dirname(policyFile), **kwargs)
        #
        # The composite objects don't seem to set these
        #
        for d in (self.mappings, self.exposures):
            d["raw"] = d["_raw"]

        LsstCamMapper._nbit_tract = 16  # These have been set to mimic the Gen3 version
        LsstCamMapper._nbit_patch = 9
        LsstCamMapper._nbit_filter = 5

        LsstCamMapper._nbit_id = 64 - (LsstCamMapper._nbit_tract + 2*LsstCamMapper._nbit_patch
                                       + LsstCamMapper._nbit_filter)

        baseFilters = set()
        baseBands = set()
        self.bandToIdNumDict = {}  # this is to get rid of afwFilter.getId calls
        filterNum = -1
        for filterDef in self.filterDefinitions:
            band = filterDef.band
            physical_filter = filterDef.physical_filter
            baseFilters.add(physical_filter)
            baseBands.add(band)
            if physical_filter not in self.bandToIdNumDict:
                filterNum += 1
                self.bandToIdNumDict[physical_filter] = filterNum
            if band not in self.bandToIdNumDict:
                self.bandToIdNumDict[band] = filterNum

        nFilter = len(baseBands)
        if nFilter >= 2**LsstCamMapper._nbit_filter:
            raise RuntimeError("You have more filters (%d) defined than fit into the %d bits allocated" %
                               (nFilter, LsstCamMapper._nbit_filter))

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
        tract = int(dataId["tract"])
        if tract < 0 or tract >= 2**LsstCamMapper._nbit_tract:
            raise RuntimeError("tract not in range [0, %d)" % (2**LsstCamMapper._nbit_tract))
        patchX, patchY = [int(patch) for patch in dataId["patch"].split(",")]
        for p in (patchX, patchY):
            if p < 0 or p >= 2**LsstCamMapper._nbit_patch:
                raise RuntimeError("patch component not in range [0, %d)" % 2**LsstCamMapper._nbit_patch)
        oid = (((tract << LsstCamMapper._nbit_patch) + patchX) << LsstCamMapper._nbit_patch) + patchY
        if singleFilter:
            if self.bandToIdNumDict[dataId["filter"]] >= 2**LsstCamMapper._nbit_filter:
                raise RuntimeError("Filter %s has too high an ID (%d) to fit in %d bits",
                                   dataId["filter"], self.bandToIdNumDict[dataId["filter"]],
                                   LsstCamMapper._nbit_filter)
            return (oid << LsstCamMapper._nbit_filter) + self.bandToIdNumDict[dataId["filter"]]
        return oid

    def bypass_ccdExposureId_bits(self, datasetType, pythonType, location, dataId):
        """How many bits are required for the maximum exposure ID"""
        return 34  # To match the value computed in gen3

    def bypass_deepCoaddId_bits(self, *args, **kwargs):
        """The number of bits used up for patch ID bits."""
        return LsstCamMapper._nbit_id

    def bypass_deepMergedCoaddId_bits(self, *args, **kwargs):
        """The number of bits used up for patch ID bits."""
        return LsstCamMapper._nbit_id - LsstCamMapper._nbit_filter


class ImsimParseTask(LsstCamParseTask):
    """Parser suitable for imsim data.
    """

    _mapperClass = ImsimMapper
    _translatorClass = LsstCamImSimTranslator

    def translate_controller(self, md):
        """Always return Simulation as controller for imsim data."""
        return "S"
