# This file is part of obs_lsst.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from lsst.daf.butler import Butler
from lsst.ip.isr import Defects
import lsst.obs.lsst as ol

# Read and put new manual defects into the butler.
# We have to use embargo_old because
# this is where the CP needed for defects are.
camera_name = 'LSSTComCam'
butler = Butler('/repo/embargo_old', writeable=True)
collection_output = 'LSSTComCam/calib/DM-47365/addManualDefects/manualDefects.20241121c/run'
butler.registry.registerRun(collection_output)

cc = ol.LsstComCam
camera = cc.getCamera()
for det in camera:
    detId = det.getId()
    detName = det.getName()

    # This is only valid for LSSTComCam which has a single raft
    manual_defects = \
        Defects.readText('obs_lsst_data/comCam/manual_defects/r22_s'+detName[5:]+'/20241120T000000.ecsv')

    butler.put(manual_defects, "manual_defects",
               instrument="LSSTComCam", detector=detId,
               run=collection_output)
