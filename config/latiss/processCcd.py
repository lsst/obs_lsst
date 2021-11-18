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
"""
latiss-specific overrides for ProcessCcdTask
"""
import os.path

ObsConfigDir = os.path.dirname(__file__)

for sub in ("isr", "charImage", "calibrate"):
    path = os.path.join(ObsConfigDir, sub + ".py")
    if os.path.exists(path):
        getattr(config, sub).load(path)

import os
from lsst.utils import getPackageDir
from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask
from lsst.obs.lsst.filters import LATISS_FILTER_DEFINITIONS

REFCAT_NAME = 'gaia'
# REFCAT_NAME = 'ps1'

if REFCAT_NAME == 'gaia':
    REFCAT = "gaia_dr2_20191105"
    config.calibrate.doPhotoCal = False
else:
    REFCAT = "ps1_pv3_3pi_20170110"


# Reference catalog
# config.calibrate.refObjLoader.retarget(LoadIndexedReferenceObjectsTask)
# config.calibrate.refObjLoader.load(os.path.join(getPackageDir("obs_lsst"), "config", "filterMap.py"))

# config.calibrate.refObjLoader.ref_dataset_name="cal_ref_cat"
config.calibrate.connections.astromRefCat = REFCAT
config.calibrate.connections.photoRefCat = REFCAT

for refObjLoader in (config.charImage.refObjLoader,
                     config.calibrate.astromRefObjLoader,
                     config.calibrate.photoRefObjLoader):
    refObjLoader.retarget(LoadIndexedReferenceObjectsTask)
    refObjLoader.ref_dataset_name = REFCAT

filtMap = {}
filts = LATISS_FILTER_DEFINITIONS
if REFCAT_NAME == 'gaia':
    for filt in filts._filters:
        filtMap[filt.band] = 'phot_g_mean'

else:  # Pan-STARRS:
    # TODO: add a mag limit here - it's super slow without it
    for filt in filts._filters:
        if len(filt.band) == 1:  # skip 'white' etc
            filtMap[filt.band] = filt.band


config.calibrate.astromRefObjLoader.filterMap = filtMap
config.calibrate.photoRefObjLoader.filterMap = filtMap

config.charImage.doDeblend = False
config.calibrate.doDeblend = False
