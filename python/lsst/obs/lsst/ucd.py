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


def computeVisit(dateObs):
    """Compute a visit number from the full dateObs"""

    fullDateTime = datetime.datetime.strptime(dateObs + "+0000", "%Y-%m-%dT%H:%M:%S.%f%z")
    visit = int((fullDateTime - ROLLOVERTIME - TZERO).total_seconds())

    return visit


class UcdMapper(LsstCamMapper):
    """The Mapper for the ucd camera."""

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
            visit = computeVisit(dataId['dateObs'])
        detector = self._extractDetectorName(dataId)

        return 10*visit + detector


class UcdParseTask(LsstCamParseTask):
    """Parser suitable for ucd data.

    We need this to parse the UC Davis headers.
    There's information we need from the filename, so we need to override getInfo
    and provide some translation methods
    """

    _cameraClass = Ucd           # the class to instantiate for the class-scope camera

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
        return 'RTM-999'

    def translate_detector(self, md):
        """Find the detector number from the serial

        This should come from CHIPID, not LSST_NUM
        """
        raftName = 'RTM-999'
        # raftName = self._translate_raftName(md.get("RAFTNAME"))
        serial = md.get("LSST_NUM")

        # this seems to be appended more or less at random, and breaks the mapping dict
        if serial.endswith('-Dev'):
            serial = serial[:-4]

        # a dict of dicts holding the raft serials
        raftSerialData = {
            'RTM-999': {  # Dummy Raft for UC Davis data
                'E2V-CCD250-112-04': 0,  # S00
                'ITL-3800C-029': 1,  # S01
                'ITL-3800C-002': 2,  # S02
                'E2V-CCD250-165': 3,  # S10
                'E2V-CCD250-130': 4,  # S11
                'E2V-CCD250-153': 5,  # S12
                'E2V-CCD250-163': 6,  # S20
                'E2V-CCD250-216': 7,  # S21
                'E2V-CCD250-252': 8   # S22
            },
        }
        return raftSerialData[raftName][serial]

    def translate_filter(self, md):
        """Generate a filtername from FILTER

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        filter : `str`
            Filter name
        """

        filter = md.get("FILTER")
        try:
            return {
                'g': 'g',
                'r': 'r',
                'i': 'i',
                'z': 'z',
                'y': 'y',
                'G': 'g',
                'R': 'r',
                'I': 'i',
                'Z': 'z',
                'Y': 'y',
            }[filter]
        except KeyError:
            print("Unknown filter (assuming NONE): %s" % (filter))
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

    def translate_dateObs(self, md):
        """Get a legal dateObs by parsing DATE-OBS

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        dateObs : `str`
            The day that the data was taken, e.g. 2018-08-20T21:56:24.608
        """

        d = datetime.datetime.strptime(md.get("DATE-OBS"), "%a %b %d %H:%M:%S %Z %Y")
        dateObs = d.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        return dateObs

    def translate_dayObs(self, md):
        """Generate the day that the observation was taken

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        dayObs : `str`
            The day that the data was taken, e.g. 1958-02-05
        """
        dateObs = self.translate_dateObs(md)

        d = datetime.datetime.strptime(dateObs + "+0000", "%Y-%m-%dT%H:%M:%S.%f%z")
        d -= ROLLOVERTIME
        dayObs = d.strftime("%Y-%m-%d")

        return dayObs

    def translate_runNum(self, md):
        """Generate a run number from the date

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        run : `int`
        """
        run = self.translate_dayObs(md)
        return run
