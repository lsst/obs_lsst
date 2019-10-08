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
from . import LsstCamMapper, LsstCamMakeRawVisitInfo
from .latiss import LatissMapper
from .ingest import LsstCamParseTask
from .translators import LsstUCDCamTranslator

__all__ = ["UcdMapper", "UcdParseTask"]


class UcdMakeRawVisitInfo(LsstCamMakeRawVisitInfo):
    """Make a VisitInfo from the FITS header of a raw image."""
    metadataTranslator = LsstUCDCamTranslator


class UcdMapper(LsstCamMapper):
    """The Mapper for the UCDavis camera."""
    translatorClass = LsstUCDCamTranslator
    MakeRawVisitInfoClass = UcdMakeRawVisitInfo

    _cameraName = "ucd"
    yamlFileList = ["ucd/ucdMapper.yaml"] + \
        list(LatissMapper.yamlFileList) + list(LsstCamMapper.yamlFileList)

    def _extractDetectorName(self, dataId):
        if 'detectorName' in dataId:
            detectorName = dataId['detectorName']
        else:
            detectorName = LsstUCDCamTranslator.DETECTOR_NAME
        if 'raftName' in dataId:
            raftName = dataId['raftName']
        else:
            raftName = LsstUCDCamTranslator.compute_detector_group_from_num(dataId['detector'])
        return f"{raftName}_{detectorName}"

    def bypass_ccdExposureId_bits(self, datasetType, pythonType, location, dataId):
        """How many bits are required for the maximum exposure ID"""
        return 48  # max detector_exposure_id ~ 203012122359590


class UcdParseTask(LsstCamParseTask):
    """Parser suitable for UCD data.

    We need this to parse the UC Davis headers.
    """

    _mapperClass = UcdMapper
    _translatorClass = LsstUCDCamTranslator

    def translate_testSeqNum(self, md):
        """Translate the sequence number

        Sometimes this is present, sometimes it is not. When it is, return it
        as an int. When it's not, provide a default value of 0 as an int.
        This function exists because currently the Gen2 butler's default
        value providing pathway has trouble with types.

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            Image metadata.

        Returns
        -------
        seqNum : `int`
            The seqNum, with a default value of 0 if required
        """
        try:
            seqNum = int(md.getScalar("SEQNUM"))
        except KeyError:
            seqNum = 0
        return seqNum
