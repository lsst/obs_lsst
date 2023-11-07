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

"""LATISS-specific overrides for MakeWarpTask"""

# These thresholds must be relaxed for AuxTel/LATISS compared to the task
# defaults (which were conditioned on HSC data).  These have been chosen
# based on the data observed in the 2022-11B (PREOPS-1986) and 2022-12A
# (PREOPS-3135) runs (see figures on DM-37497) and are probably going to
# evolve as the commissioning of AuxTel procedes.
config.select.maxEllipResidual = 0.1
# Updated with DM-40668
config.select.maxScaledSizeScatter = 0.025
config.select.maxPsfTraceRadiusDelta = 4.8
