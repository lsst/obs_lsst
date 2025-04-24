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
LATISS-specific overrides for IsrTaskLSST
"""
import numpy as np


config.overscanCamera.defaultDetectorConfig.defaultAmpConfig.saturation = 120000

config.crosstalk.doQuadraticCrosstalkCorrection = False
config.crosstalk.doSubtrahendMasking = True
config.crosstalk.minPixelToMask = 1.0
config.doDeferredCharge = False
config.doBrighterFatter = False
# Maintain compatibility with existing calibrations.
poscan = config.overscanCamera.defaultDetectorConfig.defaultAmpConfig.parallelOverscanConfig
poscan.doAbsoluteMaxDeviation = True
poscan.doMedianSmoothingOutlierRejection = False

config.cameraKeywordsToCompare = ["SEQNAME", "SEQFILE", "SEQCKSUM", "ODP", "AP0_RC", "TEMP_SET"]

config.serialOverscanMedianShiftSigmaThreshold = np.inf
config.bssVoltageMinimum = 0.0
