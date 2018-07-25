#
# LSST Data Management System
# Copyright 2016 LSST Corporation.
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
"""The AuxTelCam Mapper."""  # necessary to suppress D100 flake8 warning.

import os

from . import auxTel
from . import LsstCamMapper

__all__ = ["AuxTelMapper"]
    
class AuxTelMapper(LsstCamMapper):
    """The Mapper for the auxTel camera."""

    yamlFileList =  ["auxTelMapper.yaml"] + list(LsstCamMapper.yamlFileList)

    @classmethod
    def getCameraName(cls):
        return "auxTel"

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing the camera geometry."""
        return auxTel.AuxTelCam()

    def _extractDetectorName(self, dataId):
        return 0 # "S1"
