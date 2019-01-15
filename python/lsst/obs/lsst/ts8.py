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
import re
from lsst.obs.base.yamlCamera import YamlCamera
from . import LsstCamMapper, LsstCamMakeRawVisitInfo
from .auxTel import AuxTelMapper
from .ingest import LsstCamParseTask, EXTENSIONS
from .translators import LsstTS8Translator

__all__ = ["Ts8Mapper", "Ts8", "Ts8ParseTask"]


class Ts8(YamlCamera):
    """The ts8's single raft Camera
    """
    packageName = 'obs_lsst'

    def __init__(self, cameraYamlFile=None):
        """Construct lsstCam for ts8
        """
        pass


class Ts8MakeRawVisitInfo(LsstCamMakeRawVisitInfo):
    """Make a VisitInfo from the FITS header of a raw image."""
    metadataTranslator = LsstTS8Translator


class Ts8Mapper(LsstCamMapper):
    """The Mapper for the ts8 camera."""
    MakeRawVisitInfoClass = Ts8MakeRawVisitInfo
    yamlFileList = ["ts8/ts8Mapper.yaml"] + \
        list(AuxTelMapper.yamlFileList) + list(LsstCamMapper.yamlFileList)

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing the camera geometry."""
        return Ts8()

    @classmethod
    def getCameraName(cls):
        return "ts8"

    def _extractDetectorName(self, dataId):
        if 'detectorName' in dataId:
            detectorName = dataId['detectorName']
        else:
            detectorName = LsstTS8Translator.compute_detector_name_from_num(dataId['detector'])
        detectorGroup = LsstTS8Translator.DETECTOR_GROUP_NAME
        return f"{detectorGroup}_{detectorName}"

    def _computeCcdExposureId(self, dataId):
        """Compute the 64-bit (long) identifier for a CCD exposure.

        @param dataId (dict) Data identifier including dayObs and seqNum
        """
        if len(dataId) == 0:
            return 0                    # give up.  Useful if reading files without a butler

        if 'visit' in dataId:
            visit = dataId['visit']
        else:
            visit = LsstTS8Translator.compute_exposure_id(dataId['dateObs'])
        if 'detector' in dataId:
            detector = dataId['detector']
        else:
            detector = LsstTS8Translator.compute_detector_num_from_name(dataId['detectorName'])

        return LsstTS8Translator.compute_detector_exposure_id(visit, detector)


class Ts8ParseTask(LsstCamParseTask):
    """Parser suitable for ts8 data.

    We need this because as of 2018-07-20 the headers are essentially empty and
    there's information we need from the filename, so we need to override getInfo
    and provide some translation methods
    """

    _cameraClass = Ts8           # the class to instantiate for the class-scope camera
    _translatorClass = LsstTS8Translator

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
        phuInfo, infoList = super().getInfo(filename)

        if False:
            pathname, basename = os.path.split(filename)
            basename = re.sub(r"\.(%s)$" % "|".join(EXTENSIONS), "", basename)
            phuInfo['basename'] = basename

        return phuInfo, infoList

    def translate_detectorName(self, md):
        return self.observationInfo.detector_name

    def translate_testSeqNum(self, md):
        """Translate the sequence number

        Sometimes this is present, sometimes it is not. When it is, return it
        as an int. When it's not, provide a default value of 0 as an int.
        This function exists because currently the Gen2 butler's default
        value providing pathway has trouble with types.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            image metadata

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
