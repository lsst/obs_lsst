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
from .ingest import LsstCamParseTask, EXTENSIONS

__all__ = ["AuxTelMapper", "AuxTelCam", "AuxTelParseTask"]


class AuxTelCam(YamlCamera):
    """The auxTel's single CCD Camera
    """
    packageName = 'obs_lsstCam'

    def __init__(self, cameraYamlFile=None):
        """Construct lsstCam for auxTel
        """
        if not cameraYamlFile:
            cameraYamlFile = os.path.join(utils.getPackageDir(self.packageName), "policy", "auxTel.yaml")

        YamlCamera.__init__(self, cameraYamlFile)


def computeVisit(dayObs, seqNum):
    """Compute a visit number given a dayObs and seqNum"""

    try:
        date = datetime.data.fromisoformat(dayObs)
    except AttributeError:          # requires py 3.7
        date = datetime.date(*[int(f) for f in dayObs.split('-')])

    return (date.toordinal() - 736900)*100000 + seqNum


class AuxTelMapper(LsstCamMapper):
    """The Mapper for the auxTel camera."""

    yamlFileList = ["auxTel/auxTelMapper.yaml"] + list(LsstCamMapper.yamlFileList)

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing the camera geometry."""
        return AuxTelCam()

    @classmethod
    def getCameraName(cls):
        return "auxTel"

    def _extractDetectorName(self, dataId):
        return 0                        # "S1"

    def _computeCcdExposureId(self, dataId):
        """Compute the 64-bit (long) identifier for a CCD exposure.

        @param dataId (dict) Data identifier including dayObs and seqnum
        """
        if len(dataId) == 0:
            return 0                    # give up.  Useful if reading files without a butler

        visit = computeVisit(dataId['dayObs'], dataId["seqnum"])
        detector = self._extractDetectorName(dataId)

        return 200*visit + detector


class AuxTelParseTask(LsstCamParseTask):
    """Parser suitable for auxTel data.

    We need this because as of 2018-07-20 the headers are essentially empty and
    there's information we need from the filename, so we need to override getInfo
    and provide some translation methods
    """

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

        pathname, basename = os.path.split(filename)
        basename = re.sub(r"\.(%s)$" % "|".join(EXTENSIONS), "", basename)
        phuInfo['basename'] = basename

        return phuInfo, infoList

    def translate_detector(self, md):
        return 0                        # we can't use config.parse.defaults as it only handles strings

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
        seqNum = self.translate_seqnum(md)

        return computeVisit(dayObs, seqNum)

    def translate_wavelength(self, md):
        """Translate wavelength provided by auxtel readout.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        wavelength : `int`
            The recorded wavelength as an int
        """
        return -666

    def translate_filter(self, md):
        """Translate the two filter wheels into one filter string

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        filter name : `str`
            The names of the two filters separated by a "|"; if both are empty return None
        """
        filters = []
        for k in ["FILTER1", "FILTER2"]:
            if md.exists(k):
                filters.append(md.get(k))

        filterName = "|".join(filters)

        if filterName == "":
            filterName = "NONE"

        return filterName

    def translate_seqnum(self, md):
        """Return the SEQNUM

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        the sequence number : `int`
            An identifier valid within a day
        """

        if md.exists("SEQNUM"):
            return md.get("SEQNUM")
        #
        # Oh dear.  Extract it from the filename
        #
        imgname = md.get("IMGNAME")           # e.g. AT-O-20180816-00008
        seqnum = imgname[-5:]                 # 00008
        seqnum = re.sub(r'^0+', '', seqnum)   # 8

        return int(seqnum)
