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
comCam-specific overrides for IsrTaskLSST
"""
import copy
import numpy as np


config.doSaturation = True
config.crosstalk.doQuadraticCrosstalkCorrection = True
config.crosstalk.doSubtrahendMasking = True
config.crosstalk.minPixelToMask = 1.0

config.doAmpOffset = True
config.ampOffset.doApplyAmpOffset = True
config.ampOffset.ampEdgeMaxOffset = 10.0

config.serialOverscanMedianShiftSigmaThreshold = np.inf
config.bssVoltageMinimum = 0.0

overscanCamera = config.overscanCamera

# Detector R22_S00 (0)
detectorConfig = copy.copy(overscanCamera.defaultDetectorConfig)
detectorConfig.itlDipMinWidth = 14
detectorConfig.itlDipBackgroundFraction = 0.0014
overscanCamera.detectorRules["R22_S00"] = detectorConfig

# Detector R22_S01 (1)
detectorConfig = copy.copy(overscanCamera.defaultDetectorConfig)
detectorConfig.itlDipMinWidth = 18
detectorConfig.itlDipBackgroundFraction = 0.0015
overscanCamera.detectorRules["R22_S01"] = detectorConfig

# Detector R22_S02 (2)
# No dip seen.

# Detector R22_S10 (3)
detectorConfig = copy.copy(overscanCamera.defaultDetectorConfig)
detectorConfig.itlDipMinWidth = 13
detectorConfig.itlDipBackgroundFraction = 0.00065
overscanCamera.detectorRules["R22_S10"] = detectorConfig

# Detector R22_S11 (4)
# No dip seen.

# Detector R22_S12 (5)
detectorConfig = copy.copy(overscanCamera.defaultDetectorConfig)
detectorConfig.itlDipMinWidth = 18
detectorConfig.itlDipBackgroundFraction = 0.0006
overscanCamera.detectorRules["R22_S12"] = detectorConfig

# Detector R22_S20 (6)
# No dip seen.

# Detector R22_S21 (7)
detectorConfig = copy.copy(overscanCamera.defaultDetectorConfig)
detectorConfig.itlDipMinWidth = 14
detectorConfig.itlDipMinHeight = 30
detectorConfig.itlDipBackgroundFraction = 0.0006
overscanCamera.detectorRules["R22_S21"] = detectorConfig

# Detector R22_S22 (8)
detectorConfig = copy.copy(overscanCamera.defaultDetectorConfig)
detectorConfig.itlDipMinWidth = 4
detectorConfig.itlDipBackgroundFraction = 0.0026
overscanCamera.detectorRules["R22_S22"] = detectorConfig
