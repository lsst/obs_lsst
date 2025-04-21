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

# ITL dip handling.  The defaultDetectorConfig has a
# itlDipBackgroundFraction of 0.0, which disables the correction.
# This means we only need to update the rules for detectors that show
# evidence of the features.  To simplify this for the initial
# configuration, define three configurations that have "small",
# "medium", and "big" corrections, and assign those to the detectors
# as needed.
smallCorrectionConfig = copy.copy(config.overscanCamera.defaultDetectorConfig)
smallCorrectionConfig.itlDipMinWidth = 18
smallCorrectionConfig.itlDipBackgroundFraction = 0.0005

mediumCorrectionConfig = copy.copy(config.overscanCamera.defaultDetectorConfig)
mediumCorrectionConfig.itlDipMinWidth = 13
mediumCorrectionConfig.itlDipBackgroundFraction = 0.0015

largeCorrectionConfig = copy.copy(config.overscanCamera.defaultDetectorConfig)
largeCorrectionConfig.itlDipMinWidth = 8
largeCorrectionConfig.itlDipBackgroundFraction = 0.0025

# Small corrections:
# det 3
config.overscanCamera.detectorRules["R01_S10"] = copy.copy(smallCorrectionConfig)
# det 8
config.overscanCamera.detectorRules["R01_S22"] = copy.copy(smallCorrectionConfig)
# det 11
config.overscanCamera.detectorRules["R02_S02"] = copy.copy(smallCorrectionConfig)
# det 13
config.overscanCamera.detectorRules["R02_S11"] = copy.copy(smallCorrectionConfig)
# det 16
config.overscanCamera.detectorRules["R02_S21"] = copy.copy(smallCorrectionConfig)
# det 20
config.overscanCamera.detectorRules["R03_S20"] = copy.copy(smallCorrectionConfig)
# det 165
config.overscanCamera.detectorRules["R41_S10"] = copy.copy(smallCorrectionConfig)

# Medium corrections:
# det 4
config.overscanCamera.detectorRules["R01_S11"] = copy.copy(mediumCorrectionConfig)
# det 5
config.overscanCamera.detectorRules["R01_S12"] = copy.copy(mediumCorrectionConfig)
# det 7
config.overscanCamera.detectorRules["R01_S21"] = copy.copy(mediumCorrectionConfig)
# det 14
config.overscanCamera.detectorRules["R02_S12"] = copy.copy(mediumCorrectionConfig)
# det 24
config.overscanCamera.detectorRules["R03_S20"] = copy.copy(mediumCorrectionConfig)
# det 30
config.overscanCamera.detectorRules["R10_S10"] = copy.copy(mediumCorrectionConfig)
# det 162
config.overscanCamera.detectorRules["R41_S00"] = copy.copy(mediumCorrectionConfig)

# Large corrections:
# det 12
config.overscanCamera.detectorRules["R02_S10"] = copy.copy(largeCorrectionConfig)
# det 184
config.overscanCamera.detectorRules["R43_S11"] = copy.copy(largeCorrectionConfig)
