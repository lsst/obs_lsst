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
imsim-specific overrides for CalibrateTask
"""
import os.path

configDir = os.path.dirname(__file__)

# Reference catalog overrides for simulated data.
for refObjLoader in (config.astromRefObjLoader,
                     config.photoRefObjLoader,
                     ):
    refObjLoader.load(os.path.join(configDir, 'filterMap.py'))
    # Use the filterMap instead of the "any" filter.
    refObjLoader.anyFilterMapsToThis = None

config.connections.astromRefCat = "cal_ref_cat"
config.connections.photoRefCat = "cal_ref_cat"

# No color term in simulation at the moment
config.photoCal.applyColorTerms = False
config.photoCal.match.referenceSelection.doMagLimit = True
config.photoCal.match.referenceSelection.magLimit.fluxField = "lsst_i_smeared_flux"
config.photoCal.match.referenceSelection.magLimit.maximum = 22.0
# select only stars for photometry calibration
config.photoCal.match.sourceSelection.unresolved.maximum = 0.5

# Additional configs for star+galaxy ref cats post DM-17917
config.astrometry.referenceSelector.doUnresolved = True
config.astrometry.referenceSelector.unresolved.name = "resolved"
config.astrometry.referenceSelector.unresolved.minimum = None
config.astrometry.referenceSelector.unresolved.maximum = 0.5

config.astrometry.doMagnitudeOutlierRejection = True
# Set threshold above which astrometry will be considered a failure (DM-32129)
config.astrometry.maxMeanDistanceArcsec = 0.05

# Reduce Chebyshev polynomial order for background fitting (DM-30820)
config.detection.background.approxOrderX = 1
config.detection.tempLocalBackground.approxOrderX = 1
config.detection.tempWideBackground.approxOrderX = 1

# Make sure galaxies are not used for zero-point calculation.
config.photoCal.match.referenceSelection.doUnresolved = True
config.photoCal.match.referenceSelection.unresolved.name = "resolved"
config.photoCal.match.referenceSelection.unresolved.minimum = None
config.photoCal.match.referenceSelection.unresolved.maximum = 0.5

# S/N cuts for zero-point calculation source selection
config.photoCal.match.sourceSelection.doSignalToNoise = True
config.photoCal.match.sourceSelection.signalToNoise.minimum = 150
config.photoCal.match.sourceSelection.signalToNoise.fluxField = "base_PsfFlux_instFlux"
config.photoCal.match.sourceSelection.signalToNoise.errField = "base_PsfFlux_instFluxErr"
