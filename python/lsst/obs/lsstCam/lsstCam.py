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
from __future__ import division, print_function
import os.path
import lsst.utils as utils
from lsst.obs.base.yamlCamera import YamlCamera


class comCam(YamlCamera):
    """comCam
    """
    
    packageName = 'obs_comCam'
    
    def __init__(self, cameraYamlFile=None):
        """Construct comCam
        """
        if not cameraYamlFile:
            cameraYamlFile = os.path.join(utils.getPackageDir(self.packageName), "policy", "comCam.yaml")
        
        YamlCamera.__init__(self, cameraYamlFile)
            

class LsstCam(YamlCamera):
    """The real LSST 3.2Gpix Camera
    """
    packageName = 'obs_lsstCam'

    def __init__(self, cameraYamlFile=None):
        """Construct lsstCam
        """
        if not cameraYamlFile:
            cameraYamlFile = os.path.join(utils.getPackageDir(self.packageName), "policy", "lsstCam.yaml")

        YamlCamera.__init__(self, cameraYamlFile)

class ImsimCam(YamlCamera):
    """The imsim realisation of the real LSST 3.2Gpix Camera
    """
    packageName = 'obs_lsstCam'

    def __init__(self, cameraYamlFile=None):
        """Construct lsstCam for imsim
        """
        if not cameraYamlFile:
            cameraYamlFile = os.path.join(utils.getPackageDir(self.packageName), "policy", "imsim.yaml")

        YamlCamera.__init__(self, cameraYamlFile)

class PhosimCam(YamlCamera):
    """The phosim realisation of the real LSST 3.2Gpix Camera
    """
    packageName = 'obs_lsstCam'

    def __init__(self, cameraYamlFile=None):
        """Construct lsstCam for phosim
        """
        if not cameraYamlFile:
            cameraYamlFile = os.path.join(utils.getPackageDir(self.packageName), "policy", "phosim.yaml")

        YamlCamera.__init__(self, cameraYamlFile)
