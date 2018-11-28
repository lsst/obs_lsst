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
from .ingest import LsstCamParseTask, EXTENSIONS, ROLLOVERTIME, TZERO

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


def computeVisit(dateObs):
    """Compute a visit number from the full dateObs"""

    fullDateTime = datetime.datetime.strptime(dateObs + "+0000", "%Y-%m-%dT%H:%M:%S.%f%z")
    visit = int((fullDateTime - ROLLOVERTIME - TZERO).total_seconds())

    return visit


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
            visit = computeVisit(dataId['dateObs'])
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

    def _translate_raftName(self, raftString):
        """Get the raft name from the string in the header"""
        # should look something like 'LCA-11021_RTM-011-Dev'
        return raftString[10:17]

    def translate_detector(self, md):
        """Find the detector number from the serial

        This should come from CHIPID, not LSST_NUM
        """
        raftName = self._translate_raftName(md.get("RAFTNAME"))
        serial = md.get("LSST_NUM")

        # this seems to be appended more or less at random, and breaks the mapping dict
        if serial.endswith('-Dev'):
            serial = serial[:-4]

        # a dict of dicts holding the raft serials
        raftSerialData = {
            'RTM-002': {  # config for RTM-004 aka ETU #1
                'ITL-3800C-023': 0,  # S00
                'ITL-3800C-032': 1,  # S01
                'ITL-3800C-042': 2,  # S02
                'ITL-3800C-090': 3,  # S10
                'ITL-3800C-107': 4,  # S11
                'ITL-3800C-007': 5,  # S12
                'ITL-3800C-004': 6,  # S20
                'ITL-3800C-139': 7,  # S21
                'ITL-3800C-013': 8   # S22
            },
            'RTM-003': {  # config for RTM-004 aka ETU #2
                'ITL-3800C-145': 0,  # S00
                'ITL-3800C-022': 1,  # S01
                'ITL-3800C-041': 2,  # S02
                'ITL-3800C-100': 3,  # S10
                'ITL-3800C-017': 4,  # S11
                'ITL-3800C-018': 5,  # S12
                'ITL-3800C-102': 6,  # S20
                'ITL-3800C-146': 7,  # S21
                'ITL-3800C-103': 8   # S22
            },
            'RTM-004': {  # config for RTM-004 aka RTM #1
                'ITL-3800C-381': 0,  # S00
                'ITL-3800C-333': 1,  # S01
                'ITL-3800C-380': 2,  # S02
                'ITL-3800C-346': 3,  # S10
                'ITL-3800C-062': 4,  # S11
                'ITL-3800C-371': 5,  # S12
                'ITL-3800C-385': 6,  # S20
                'ITL-3800C-424': 7,  # S21
                'ITL-3800C-247': 8   # S22
            },
            'RTM-005': {  # config for RTM-005 aka RTM #2
                'E2V-CCD250-220': 0,  # S00
                'E2V-CCD250-239': 1,  # S01
                'E2V-CCD250-154': 2,  # S02
                'E2V-CCD250-165': 3,  # S10
                'E2V-CCD250-130': 4,  # S11
                'E2V-CCD250-153': 5,  # S12
                'E2V-CCD250-163': 6,  # S20
                'E2V-CCD250-216': 7,  # S21
                'E2V-CCD250-252': 8   # S22
            },
            'RTM-007': {  # config for RTM-007 aka RTM #4
                'E2V-CCD250-260': 0,  # S00
                'E2V-CCD250-182': 1,  # S01
                'E2V-CCD250-175': 2,  # S02
                'E2V-CCD250-167': 3,  # S10
                'E2V-CCD250-195': 4,  # S11
                'E2V-CCD250-201': 5,  # S12
                'E2V-CCD250-222': 6,  # S20
                'E2V-CCD250-213': 7,  # S21
                'E2V-CCD250-177': 8   # S22
            },
            'RTM-008': {  # config for RTM-008 aka RTM #5
                'E2V-CCD250-160': 0,  # S00
                'E2V-CCD250-208': 1,  # S01
                'E2V-CCD250-256': 2,  # S02
                'E2V-CCD250-253': 3,  # S10
                'E2V-CCD250-194': 4,  # S11
                'E2V-CCD250-231': 5,  # S12
                'E2V-CCD250-224': 6,  # S20
                'E2V-CCD250-189': 7,  # S21
                'E2V-CCD250-134': 8   # S22
            },
            'RTM-010': {  # config for RTM-010 aka RTM #7
                'E2V-CCD250-266': 0,  # S00
                'E2V-CCD250-268': 1,  # S01
                'E2V-CCD250-200': 2,  # S02
                'E2V-CCD250-273': 3,  # S10
                'E2V-CCD250-179': 4,  # S11
                'E2V-CCD250-263': 5,  # S12
                'E2V-CCD250-226': 6,  # S20
                'E2V-CCD250-264': 7,  # S21
                'E2V-CCD250-137': 8,  # S22
            },
            'RTM-011': {  # config for RTM-011 aka RTM #8 NB Confluence lies here, values are from the data!
                'ITL-3800C-083': 0,  # S00
                'ITL-3800C-172': 1,  # S01
                'ITL-3800C-142': 2,  # S02
                'ITL-3800C-173': 3,  # S10
                'ITL-3800C-136': 4,  # S11
                'ITL-3800C-227': 5,  # S12
                'ITL-3800C-226': 6,  # S20
                'ITL-3800C-230': 7,  # S21
                'ITL-3800C-235': 8,  # S22
            },
            'RTM-012': {  # config for RTM-012 aka RTM #9
                'E2V-CCD250-281': 0,  # S00
                'E2V-CCD250-237': 1,  # S01
                'E2V-CCD250-234': 2,  # S02
                'E2V-CCD250-277': 3,  # S10
                'E2V-CCD250-251': 4,  # S11
                'E2V-CCD250-149': 5,  # S12
                'E2V-CCD250-166': 6,  # S20
                'E2V-CCD250-214': 7,  # S21
                'E2V-CCD250-228': 8,  # S22
            },
            'RTM-014': {  # config for RTM-014 aka RTM #11
                'ITL-3800C-307': 0,  # S00
                'ITL-3800C-325': 1,  # S01
                'ITL-3800C-427': 2,  # S02
                'ITL-3800C-361': 3,  # S10
                'ITL-3800C-440': 4,  # S11
                'ITL-3800C-411': 5,  # S12
                'ITL-3800C-400': 6,  # S20
                'ITL-3800C-455': 7,  # S21
                'ITL-3800C-407': 8,  # S22
            }
        }
        return raftSerialData[raftName][serial]

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

        try:
            filterPos = md.get("FILTPOS")
        except KeyError:
            print("FILTPOS key not found in header (assuming NONE)")
            return "NONE"

        try:
            return {
                2: 'g',
                3: 'r',
                4: 'i',
                5: 'z',
                6: 'y',
            }[filterPos]
        except KeyError:
            print("Unknown filterPos (assuming NONE): %d" % (filterPos))
            return "NONE"

    def translate_visit(self, md):
        """Generate a unique visit number

        Note that SEQNUM is not unique for a given day in TS8 data
        so instead we use the number of seconds since TZERO as defined in
        the main LSST part of the package.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        visit_num : `int`
            Visit number, as translated
        """
        dateObs = self.translate_dateObs(md)

        return computeVisit(dateObs)

    def translate_testSeqNum(self, md):
        """Translate the sequence number

        Sometimes this is present, sometimes it is not. When it is, return it
        as an int. When it's not, provide a default value of 0 as an int.
        This function exists because currently the Gen2 butler's default
        value providing pathway has trouble with types.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        seqNum : `int`
            The seqNum, with a default value of 0 if required
        """
        try:
            seqNum = md.get("SEQNUM")
        except KeyError:
            seqNum = 0
        return seqNum
