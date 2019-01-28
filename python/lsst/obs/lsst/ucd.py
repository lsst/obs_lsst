#
# LSST Data Management System
# Copyright 2017 LSST Corporation.
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
import os.path
import lsst.utils as utils
from lsst.obs.base.yamlCamera import YamlCamera
from . import LsstCamMapper, LsstCamMakeRawVisitInfo
from .auxTel import AuxTelMapper
from .ingest import LsstCamParseTask
from .translators import LsstUCDCamTranslator

__all__ = ["UcdMapper", "Ucd", "UcdParseTask"]


class Ucd(YamlCamera):
    """A single raft camera for UC Davis data
    """
    packageName = 'obs_lsst'

    def __init__(self, cameraYamlFile=None):
        """Construct lsstCam for ucd
        """
        if not cameraYamlFile:
            cameraYamlFile = os.path.join(utils.getPackageDir(self.packageName), "policy", "ucd.yaml")

        YamlCamera.__init__(self, cameraYamlFile)


class UcdMakeRawVisitInfo(LsstCamMakeRawVisitInfo):
    """Make a VisitInfo from the FITS header of a raw image."""
    metadataTranslator = LsstUCDCamTranslator


class UcdMapper(LsstCamMapper):
    """The Mapper for the ucd camera."""
    translatorClass = LsstUCDCamTranslator
    MakeRawVisitInfoClass = UcdMakeRawVisitInfo

    yamlFileList = ["ucd/ucdMapper.yaml"] + \
        list(AuxTelMapper.yamlFileList) + list(LsstCamMapper.yamlFileList)

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing the camera geometry."""
        return Ucd()

    @classmethod
    def getCameraName(cls):
        return "ucd"

    def _extractDetectorName(self, dataId):
        if 'detector' in dataId:
            return dataId['detector']
        else:
            detectors = ["S00", "S01", "S02", "S10", "S11", "S12", "S22", "S20", "S21", "S22"]
            return detectors.index(dataId["detectorName"])

    def _computeCcdExposureId(self, dataId):
        """Compute the 64-bit (long) identifier for a CCD exposure.

        @param dataId (dict) Data identifier including dayObs and seqNum
        """
        if len(dataId) == 0:
            return 0                    # give up.  Useful if reading files without a butler

        if 'visit' in dataId:
            visit = dataId['visit']
        else:
            pass
            # visit = computeVisit(dataId['dateObs'])
        detector = self._extractDetectorName(dataId)

        return 10*visit + detector


class UcdParseTask(LsstCamParseTask):
    """Parser suitable for ucd data.

    We need this to parse the UC Davis headers.
    There's information we need from the filename, so we need to override getInfo
    and provide some translation methods
    """

    _cameraClass = Ucd           # the class to instantiate for the class-scope camera
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
            seqNum = md.getScalar("SEQNUM")
        except KeyError:
            seqNum = 0
        return seqNum
