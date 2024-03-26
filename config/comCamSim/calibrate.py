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

import os.path

configDir = os.path.dirname(__file__)

config.connections.astromRefCat = "uw_stars_20240228"
config.connections.photoRefCat = "uw_stars_20240228"

config.astromRefObjLoader.load(os.path.join(configDir, "filterMap.py"))
config.photoRefObjLoader.load(os.path.join(configDir, "filterMap.py"))
config.astromRefObjLoader.anyFilterMapsToThis = None
config.photoRefObjLoader.anyFilterMapsToThis = None

# The following magnitude limits for reference objects used in the
# astrometric and photometric calibrations were selected to more than
# span the expected magnitude range of the icSrc catalog sources, i.e.
# those available for the calibrations (see DM-43143 for example
# distributions).  This is to avoid passing reference objects to the
# matcher that sould not be in contention for matching (thus reducing
# the chance of locking onto a bad match).
# TODO: remove (or update) once DM-43168 is implemented.
config.astrometry.referenceSelector.doMagLimit = True
config.astrometry.referenceSelector.magLimit.fluxField = "lsst_r_flux"
config.astrometry.referenceSelector.magLimit.minimum = 14.0
config.astrometry.referenceSelector.magLimit.maximum = 22.0

config.photoCal.match.referenceSelection.doMagLimit = True
config.photoCal.match.referenceSelection.magLimit.fluxField = "lsst_r_flux"
config.photoCal.match.referenceSelection.magLimit.minimum = 14.0
config.photoCal.match.referenceSelection.magLimit.maximum = 22.0

# Exposure summary stats
config.computeSummaryStats.load(os.path.join(configDir, "computeExposureSummaryStats.py"))
