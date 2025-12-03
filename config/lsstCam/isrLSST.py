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
LSSTCam-specific overrides for IsrTaskLSST
"""
import copy

config.badAmps = [
    "R42_S21_C07",  # Inconsistent linearizer and gain.
    "R03_S01_C10",  # Extremely high CTI
    "R03_S11_C00",  # Dead amp
]

config.crosstalk.doQuadraticCrosstalkCorrection = True
config.crosstalk.doSubtrahendMasking = True
config.crosstalk.minPixelToMask = 1.0

config.doAmpOffset = True
config.ampOffset.doApplyAmpOffset = False
config.ampOffset.ampEdgeMaxOffset = 10.0

# Set default brighter fatter correction to use the electrostatic
# brighter fatter correction.
config.brighterFatterCorrectionMethod = "ASTIER23"

# ITL dip handling.  The defaultDetectorConfig has a
# itlDipBackgroundFraction of 0.0, which disables the correction.
# This means we only need to update the rules for detectors that show
# evidence of the features.  To simplify this, use the five best
# configs (DM-50343 for details), and apply to the detectors as
# applicable.

correctionConfigA = copy.copy(config.overscanCamera.defaultDetectorConfig)
correctionConfigA.itlDipMinWidth = 10
correctionConfigA.itlDipBackgroundFraction = 0.0015

correctionConfigB = copy.copy(config.overscanCamera.defaultDetectorConfig)
correctionConfigB.itlDipMinWidth = 8
correctionConfigB.itlDipBackgroundFraction = 0.0030

correctionConfigC = copy.copy(config.overscanCamera.defaultDetectorConfig)
correctionConfigC.itlDipMinWidth = 13
correctionConfigC.itlDipBackgroundFraction = 0.0015

correctionConfigD = copy.copy(config.overscanCamera.defaultDetectorConfig)
correctionConfigD.itlDipMinWidth = 15
correctionConfigD.itlDipBackgroundFraction = 0.0010

correctionConfigE = copy.copy(config.overscanCamera.defaultDetectorConfig)
correctionConfigE.itlDipMinWidth = 6
correctionConfigE.itlDipBackgroundFraction = 0.0025

# A correction
# det 3
config.overscanCamera.detectorRules["R01_S10"] = correctionConfigA
# det 4
config.overscanCamera.detectorRules["R01_S11"] = correctionConfigA
# det 6
config.overscanCamera.detectorRules["R01_S20"] = correctionConfigA
# det 30
config.overscanCamera.detectorRules["R10_S10"] = correctionConfigA
# det 162
config.overscanCamera.detectorRules["R41_S00"] = correctionConfigA

# B correction
# det 5
config.overscanCamera.detectorRules["R01_S12"] = correctionConfigB

# C correction
# det 7
config.overscanCamera.detectorRules["R01_S21"] = correctionConfigC
# det 24
config.overscanCamera.detectorRules["R03_S20"] = correctionConfigC
# det 35
config.overscanCamera.detectorRules["R10_S22"] = correctionConfigC

# D correction
# det 8
config.overscanCamera.detectorRules["R01_S22"] = correctionConfigD
# det 11
config.overscanCamera.detectorRules["R02_S02"] = correctionConfigD
# det 13
config.overscanCamera.detectorRules["R02_S11"] = correctionConfigD
# det 16
config.overscanCamera.detectorRules["R02_S21"] = correctionConfigD
# det 18
config.overscanCamera.detectorRules["R03_S00"] = correctionConfigD
# det 20
config.overscanCamera.detectorRules["R03_S02"] = correctionConfigD
# det 28
config.overscanCamera.detectorRules["R10_S01"] = correctionConfigD
# det 163
config.overscanCamera.detectorRules["R41_S01"] = correctionConfigD
# det 181
config.overscanCamera.detectorRules["R43_S01"] = correctionConfigD

# E correction
# det 12
config.overscanCamera.detectorRules["R02_S10"] = correctionConfigE
# det 14
config.overscanCamera.detectorRules["R02_S12"] = correctionConfigE
# det 29
config.overscanCamera.detectorRules["R10_S02"] = correctionConfigE
# det 169
config.overscanCamera.detectorRules["R41_S21"] = correctionConfigE
# det 173
config.overscanCamera.detectorRules["R42_S02"] = correctionConfigE
# det 184
config.overscanCamera.detectorRules["R43_S11"] = correctionConfigE
# det 186
config.overscanCamera.detectorRules["R43_S20"] = correctionConfigE
