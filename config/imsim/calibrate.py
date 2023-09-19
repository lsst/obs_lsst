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

# imSim-specifc reference catalog configuration.
config.connections.astromRefCat = "cal_ref_cat"
config.connections.photoRefCat = "cal_ref_cat"
config.astromRefObjLoader.load(os.path.join(configDir, 'filterMap.py'))
config.photoRefObjLoader.load(os.path.join(configDir, 'filterMap.py'))
config.astromRefObjLoader.anyFilterMapsToThis = None

# Reduce Chebyshev polynomial order for background fitting (DM-30820)
# imsim has a constant offset background.
config.detection.background.approxOrderX = 1
config.detection.tempLocalBackground.approxOrderX = 1
config.detection.tempWideBackground.approxOrderX = 1

# DM-32129: imsim astrometry fits should be very close to the (perfect) refcat.
config.astrometry.maxMeanDistanceArcsec = 0.05

# No color terms in simulation.
config.photoCal.applyColorTerms = False

# Select only stars for photometric calibration.
config.photoCal.match.sourceSelection.unresolved.maximum = 0.5
# Brighter S/N cuts for photometric calibration source selection.
config.photoCal.match.sourceSelection.doSignalToNoise = True
config.photoCal.match.sourceSelection.signalToNoise.minimum = 150
config.photoCal.match.sourceSelection.signalToNoise.fluxField = "base_PsfFlux_instFlux"
config.photoCal.match.sourceSelection.signalToNoise.errField = "base_PsfFlux_instFluxErr"

# DM-17917: Do not use galaxies from truth catalog for astro/photo calibration.
config.astrometry.referenceSelector.doUnresolved = True
config.astrometry.referenceSelector.unresolved.name = "resolved"
config.astrometry.referenceSelector.unresolved.minimum = None
config.astrometry.referenceSelector.unresolved.maximum = 0.5
config.photoCal.match.referenceSelection.doUnresolved = True
config.photoCal.match.referenceSelection.unresolved.name = "resolved"
config.photoCal.match.referenceSelection.unresolved.minimum = None
config.photoCal.match.referenceSelection.unresolved.maximum = 0.5

# Only use brighter sources from the very deep truth catalog for photometry.
config.photoCal.match.referenceSelection.doMagLimit = True
config.photoCal.match.referenceSelection.magLimit.fluxField = "lsst_i_smeared_flux"
config.photoCal.match.referenceSelection.magLimit.maximum = 22.0
