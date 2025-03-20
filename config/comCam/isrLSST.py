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


config.doSaturation = True
config.crosstalk.doQuadraticCrosstalkCorrection = True
config.crosstalk.doSubtrahendMasking = True
config.crosstalk.minPixelToMask = 1.0

config.doAmpOffset = True
config.ampOffset.doApplyAmpOffset = True
config.ampOffset.ampEdgeMaxOffset = 10.0

overscanCamera = config.overscanCamera

# Detector R22_S22 (8)
detectorConfig = copy.copy(overscanCamera.defaultDetectorConfig)
detectorConfig.itlDipMinHeight = 50
detectorConfig.itlDipMinWidth = 5
detectorConfig.itlDipWidthScale = 1.5
detectorConfig.itlDipBackgroundFraction = 0.0026
overscanCamera.detectorRules["R22_S22"] = detectorConfig
