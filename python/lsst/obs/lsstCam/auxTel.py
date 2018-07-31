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

    
class AuxTelMapper(LsstCamMapper):
    """The Mapper for the auxTel camera."""

    yamlFileList =  ["auxTelMapper.yaml"] + list(LsstCamMapper.yamlFileList)

    @classmethod
    def getCameraName(cls):
        return "auxTel"

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing the camera geometry."""
        return AuxTelCam()

    def _extractDetectorName(self, dataId):
        return 0 # "S1"


#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

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

        # Now pull the imageType and the correct exposure time the path (no, they're not in the header)

        basenameComponents = basename.split("_")
        try:
            imageType = basenameComponents[1]
            expTime = float(basenameComponents[2])
        except IndexError:
            raise RuntimeError("File basename %s is too short to deduce expTime" % basename)

        phuInfo['imageType'] = imageType if expTime > 0 else "bias"
        phuInfo['expTime'] = expTime    # the header value is wrong

        return phuInfo, infoList
    
    def translate_detector(self, md):
        return 0                        # we can't use config.parse.defaults as it only handles strings

    def translate_visit(self, md):
        """Generate a unique visit from the timestamp.

        It might be better to use the 1000*runNo + seqNo, but the latter isn't currently set

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        visit_num : `int`
            Visit number, as translated
        """
        mjd = md.get("MJD-OBS")
        mmjd = mjd - 58300              # relative to 2018-07-01, just to make the visits a tiny bit smaller
        return int(1e5*mmjd)            # 86400s per day, so we need this resolution

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

    def translate_kid(self, md):
        """Return the end of the timestamp; the start is the day

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        the "Kirk ID" (kid) : `int`
            An identifier valid within a day
        """

        f = md.get("FILENAME")
        basename = os.path.splitext(os.path.split(f)[1])[0] # e.g. ats_exp_5_20180721023513

        tstamp = basename.split('_')[-1] # 20180721023513
        kid = tstamp[-6:]                # 023513
        kid = re.sub(r'^0+', '', kid)    # 23515

        return kid
