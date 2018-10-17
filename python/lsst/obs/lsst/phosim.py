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
from . import LsstCamMapper
from .ingest import LsstCamParseTask

__all__ = ["PhosimMapper", "PhosimCam", "PhosimParseTask"]


class PhosimCam(YamlCamera):
    """The phosim realisation of the real LSST 3.2Gpix Camera
    """
    packageName = 'obs_lsst'

    def __init__(self, cameraYamlFile=None):
        """Construct lsstCam for phosim
        """
        if not cameraYamlFile:
            cameraYamlFile = os.path.join(utils.getPackageDir(self.packageName), "policy", "phosim.yaml")

        YamlCamera.__init__(self, cameraYamlFile)


class PhosimMapper(LsstCamMapper):
    """The Mapper for the phosim simulations of the LsstCam."""

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing the camera geometry."""
        return PhosimCam()

    @classmethod
    def getCameraName(cls):
        return 'phosim'


class PhosimParseTask(LsstCamParseTask):
    """Parser suitable for phosim data.
    """

    _cameraClass = PhosimCam           # the class to instantiate for the class-scope camera

    def translate_filter(self, md):
        """Extract filter from metadata (ignoring for corner-raft chips)

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        filter : `str`
            filter name
        """
        return md.get("FILTER")

    def translate_visit(self, md):
        """Extract visit from metadata (as an int)

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        visit : `int`
            visit number
        """
        return int(md.get("OBSID"))
