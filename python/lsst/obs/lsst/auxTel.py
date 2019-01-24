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
import lsst.log
import lsst.utils as utils
from lsst.pipe.tasks.ingest import ParseTask
from lsst.obs.base.yamlCamera import YamlCamera
from . import LsstCamMapper, LsstCamMakeRawVisitInfo
from .ingest import LsstCamParseTask, EXTENSIONS
from .translators import LsstAuxTelTranslator

__all__ = ["AuxTelMapper", "AuxTelCam", "AuxTelParseTask"]


class AuxTelCam(YamlCamera):
    """The auxTel's single CCD Camera

    Parameters
    ----------
    cameraYamlFile : `str`, optional.
        Path to camera YAML file. Will default to one in this package.
    """
    packageName = 'obs_lsst'

    def __init__(self, cameraYamlFile=None):
        if not cameraYamlFile:
            cameraYamlFile = os.path.join(utils.getPackageDir(self.packageName), "policy", "auxTel.yaml")

        YamlCamera.__init__(self, cameraYamlFile)


class AuxTelMakeRawVisitInfo(LsstCamMakeRawVisitInfo):
    """Make a VisitInfo from the FITS header of a raw image."""
    metadataTranslator = LsstAuxTelTranslator


class AuxTelMapper(LsstCamMapper):
    """The Mapper for the auxTel camera."""
    MakeRawVisitInfoClass = AuxTelMakeRawVisitInfo
    yamlFileList = ["auxTel/auxTelMapper.yaml"] + list(LsstCamMapper.yamlFileList)

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera  describing the camera geometry.

        Returns
        -------
        camera : `lsst.afw.cameraGeom.Camera`
            Camera geometry.
        """
        return AuxTelCam()

    @classmethod
    def getCameraName(cls):
        """Return the camera name for this mapper."""
        return "auxTel"

    def _extractDetectorName(self, dataId):
        return f"{LsstAuxTelTranslator.DETECTOR_GROUP_NAME}_{LsstAuxTelTranslator.DETECTOR_NAME}"

    def _computeCcdExposureId(self, dataId):
        """Compute the 64-bit (long) identifier for a CCD exposure.

        Parameters
        ----------
        dataId : `dict`
            Data identifier including dayObs and seqNum

        Returns
        -------
        id : `int`
            Integer identifier for a CCD exposure.
        """
        if len(dataId) == 0:
            return 0                    # give up.  Useful if reading files without a butler

        if 'visit' in dataId:
            visit = dataId['visit']
        else:
            visit = LsstAuxTelTranslator.compute_exposure_id(dataId['dayObs'], dataId["seqNum"])

        if "detector" in dataId:
            detector = dataId["detector"]
            if detector != 0:
                lsst.log.Log.getLogger("AuxTelMapper").warn("Got detector %d for AuxTel when it should"
                                                            " always be 0", detector)
        else:
            detector = 0

        return LsstAuxTelTranslator.compute_detector_exposure_id(visit, detector)


class AuxTelParseTask(LsstCamParseTask):
    """Parser suitable for auxTel data.

    We need this because as of 2018-07-20 the headers are essentially empty and
    there's information we need from the filename, so we need to override
    `~LsstCamParseTask.getInfo` and provide some translation methods.
    """

    _cameraClass = AuxTelCam           # the class to instantiate for the class-scope camera
    _translatorClass = LsstAuxTelTranslator

    def getInfo(self, filename):
        """Get the basename and other data which is only available from the
        filename/path.

        This is horribly fragile!

        Parameters
        ----------
        filename : `str`
            The filename

        Returns
        -------
        phuInfo : `dict`
            Dictionary containing the header keys defined in the ingest config
            from the primary HDU.
        infoList : `list`
            A list of dictionaries containing the phuInfo(s) for the various
            extensions in MEF files.
        """
        phuInfo, infoList = ParseTask.getInfo(self, filename)

        pathname, basename = os.path.split(filename)
        basename = re.sub(r"\.(%s)$" % "|".join(EXTENSIONS), "", basename)
        phuInfo['basename'] = basename

        return phuInfo, infoList

    def translate_seqNum(self, md):
        """Return the sequence number.

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            Image metadata.

        Returns
        -------
        seqnum : `int`
            The sequence number identifier valid within a day.
        """

        if md.exists("SEQNUM"):
            return md.getScalar("SEQNUM")
        #
        # Oh dear.  Extract it from the filename
        #
        imgname = md.getScalar("IMGNAME")           # e.g. AT-O-20180816-00008
        seqNum = imgname[-5:]                 # 00008
        seqNum = re.sub(r'^0+', '', seqNum)   # 8

        return int(seqNum)
