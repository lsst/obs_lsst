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

"""LSSTComCamSim-specific overrides for MakeDirectWarpTask"""

# These thresholds can be tightened for the simulated data compared to the
# task defaults (which were conditioned on HSC data).  These have been
# chosen based on the OR3 dataset reduced with w_2024_19 pipeline on
# DM-37952 (see ticket for figures).
config.doSelectPreWarp = True
config.select.maxEllipResidual = 0.004
config.select.maxScaledSizeScatter = 0.014
config.select.maxPsfTraceRadiusDelta = 0.091
config.select.maxPsfApFluxDelta = 0.047
config.select.maxPsfApCorrSigmaScaledDelta = 0.041
