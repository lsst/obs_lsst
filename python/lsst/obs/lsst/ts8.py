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

    # try:
    #     # once we start using py 3.7 this will not raise, and this try block
    #     # can be removed. Until then, this will raise an AttributeError
    #     # and therefore fall through to the except block which does it the
    #     # ugly and hard-to-understand py <= 3.6 way
    #     date = datetime.data.fromisoformat(dayObs)
    # except AttributeError:
    #     date = datetime.date(*[int(f) for f in dayObs.split('-')])

    # return (date.toordinal() - 730000)*100000 + seqNum
    return visit  # xxx fix return!


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

    def translate_detector(self, md):
        """Find the detector number

        This should come from CHIPID, not LSST_NUM
        """
        serial = md.get("LSST_NUM")

        return {  # config for RTM-007 aka RTM #4
            'E2V-CCD250-260': 0,  # S00
            'E2V-CCD250-182': 1,  # S01
            'E2V-CCD250-175': 2,  # S02
            'E2V-CCD250-167': 3,  # S10
            'E2V-CCD250-195': 4,  # S11
            'E2V-CCD250-201': 5,  # S12
            'E2V-CCD250-222': 6,  # S20
            'E2V-CCD250-213': 7,  # S21
            'E2V-CCD250-177': 8,  # S22
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
        so instead we use the number of seconds into the day
        and the dayObs. We take the ROLLOVER time from the main
        LSST configuration.

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
        # dayObs = self.translate_dayObs(md)

        # fullDateTime = datetime.datetime.strptime(dateObs + "+0000", "%Y-%m-%dT%H:%M:%S.%f%z")
        # justTime = datetime.datetime.strptime(dateObs.split('T')[0], "%Y-%m-%d")
        # justTime = justTime.replace(tzinfo=fullDateTime.tzinfo)  # turn into a timedelta obj

        # fullDateTime -= ROLLOVERTIME
        # secondsIntoDay = (fullDateTime - justTime).total_seconds()

        return computeVisit(dateObs)
