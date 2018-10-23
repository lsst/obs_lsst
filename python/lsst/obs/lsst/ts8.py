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
import datetime
import os.path
import re
import lsst.utils as utils
from lsst.pipe.tasks.ingest import ParseTask
from lsst.obs.base.yamlCamera import YamlCamera
from . import LsstCamMapper
from .auxTel import AuxTelMapper
from .ingest import LsstCamParseTask, EXTENSIONS

__all__ = ["Ts8Mapper", "Ts8", "Ts8ParseTask"]


class Ts8(YamlCamera):
    """The ts8's single raft Camera
    """
    packageName = 'obs_lsst'

    def __init__(self, cameraYamlFile=None):
        """Construct lsstCam for ts8
        """
        if not cameraYamlFile:
            cameraYamlFile = os.path.join(utils.getPackageDir(self.packageName), "policy", "ts8.yaml")

        YamlCamera.__init__(self, cameraYamlFile)


def computeVisit(dayObs, seqNum):
    """Compute a visit number given a dayObs and seqNum"""

    try:
        date = datetime.data.fromisoformat(dayObs)
    except AttributeError:          # requires py 3.7
        date = datetime.date(*[int(f) for f in dayObs.split('-')])

    return (date.toordinal() - 730000)*100000 + seqNum


class Ts8Mapper(LsstCamMapper):
    """The Mapper for the ts8 camera."""

    yamlFileList = ["ts8/ts8Mapper.yaml"] + \
        list(AuxTelMapper.yamlFileList) + list(LsstCamMapper.yamlFileList)

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing the camera geometry."""
        return Ts8()

    @classmethod
    def getCameraName(cls):
        return "ts8"

    def _extractDetectorName(self, dataId):
        return dataId['detector']

    def _computeCcdExposureId(self, dataId):
        """Compute the 64-bit (long) identifier for a CCD exposure.

        @param dataId (dict) Data identifier including dayObs and seqNum
        """
        if len(dataId) == 0:
            return 0                    # give up.  Useful if reading files without a butler

        visit = computeVisit(dataId['dayObs'], dataId["seqNum"])
        detector = self._extractDetectorName(dataId)

        return 10*visit + detector


class Ts8ParseTask(LsstCamParseTask):
    """Parser suitable for ts8 data.

    We need this because as of 2018-07-20 the headers are essentially empty and
    there's information we need from the filename, so we need to override getInfo
    and provide some translation methods
    """

    _cameraClass = Ts8           # the class to instantiate for the class-scope camera

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

        if False:
            pathname, basename = os.path.split(filename)
            basename = re.sub(r"\.(%s)$" % "|".join(EXTENSIONS), "", basename)
            phuInfo['basename'] = basename

        return phuInfo, infoList

    def translate_detectorName(self, md):
        detector = self.translate_detector(md)

        return ["S00", "S01", "S02",
                "S10", "S11", "S12",
                "S20", "S21", "S22"][detector]

    def translate_detector(self, md):
        """Find the detector number

        This should come from CHIPID, not LSST_NUM
        """
        serial = md.get("LSST_NUM")

        return {
            'E2V-CCD250-266-Dev': 0,  # S00
            'E2V-CCD250-268-Dev': 1,  # S01
            'E2V-CCD250-200-Dev': 2,  # S02
            'E2V-CCD250-273-Dev': 3,  # S10
            'E2V-CCD250-179': 4,  # S11
            'E2V-CCD250-263-Dev': 5,  # S12
            'E2V-CCD250-226-Dev': 6,  # S20
            'E2V-CCD250-264-Dev': 7,  # S21
            'E2V-CCD250-137-Dev': 8,  # S22
        }[serial]

    def translate_filter(self, md):
        """Generate a filtername from a FILTPOS

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        filter : `str`
            Filter name
        """

        filterPos = md.get("FILTPOS")
        try:
            return {
                5: 'z',
                6: 'y',
            }[filterPos]
        except IndexError:
            print("Unknown filterPos (assuming NONE): %d" % (filterPos))
            return "NONE"

    def translate_visit(self, md):
        """Generate a unique visit number

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        visit_num : `int`
            Visit number, as translated
        """
        dayObs = self.translate_dayObs(md)
        seqNum = md.get("SEQNUM")

        return computeVisit(dayObs, seqNum)
