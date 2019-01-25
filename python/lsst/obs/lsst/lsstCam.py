# This file is part of obs_lsst.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
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

__all__ = ("LsstCam",)

import os.path
import lsst.utils as utils
from lsst.obs.base.yamlCamera import YamlCamera


class LsstCam(YamlCamera):
    """The real LSST 3.2Gpix Camera

    Parameters
    ----------
    cameraYamlFile : `str`, optional
        Path to camera YAML file. Will default to one in this package.
    """
    packageName = 'obs_lsst'

    def __init__(self, cameraYamlFile=None):
        if not cameraYamlFile:
            cameraYamlFile = os.path.join(utils.getPackageDir(self.packageName), "policy", "lsstCam.yaml")

        YamlCamera.__init__(self, cameraYamlFile)
