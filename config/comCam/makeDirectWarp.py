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

"""LSSTComCam-specific overrides for MakeDirectWarpTask"""

# These thresholds have been conditioned on the latest DRP run (DM-48371)
# which used the w_2025_02 pipeline and the LSSTComCam/DP1-RC1/defaults
# collection.
# Keep these in sync with the makeWarp.py config.
config.select.maxEllipResidual = 0.0055
config.select.maxScaledSizeScatter = 0.017
config.select.maxPsfTraceRadiusDelta = 4.4
config.select.maxPsfApFluxDelta = 1.6
config.select.maxPsfApCorrSigmaScaledDelta = 0.13
