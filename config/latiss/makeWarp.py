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
# evolve as the commissioning of AuxTel proceeds.  Further updated for
# DM-40668....and the latest update is based on a reassessment as part of
# the addition of two additional metrics on DM-37952 using the data
# satisfying:
#      (exposure.day_obs>=20230509 AND exposure.day_obs<=20240513) AND
#      (exposure.observation_type='science') AND
#      (exposure.science_program='AUXTEL_PHOTO_IMAGING' OR
#       exposure.science_program='AUXTEL_DRP_IMAGING')"
config.select.maxEllipResidual = 0.027
config.select.maxScaledSizeScatter = 0.026
config.select.maxPsfTraceRadiusDelta = 2.9
config.select.maxPsfApFluxDelta = 0.075
config.select.maxPsfApCorrSigmaScaledDelta = 0.118

# PSF-matching configs are in units of pix and specific to skymap pixel scale

# Max PSF FWHM allowed into coadds BestSeeingSelectVisits.maxPsfFwhm = 1.9
# If skymap pixel scale is 0.1, that translates to Fwhm of 19.0
# TO DO: Change this to 9.5 if we go to 0.2 pixel scale.
config.modelPsf.defaultFwhm = 19.0

config.warpAndPsfMatch.psfMatch.kernel["AL"].kernelSize = config.matchingKernelSize

# These configs are for skymaps of pixel scale 0.1
# TO DO: Delete these 3 if we go a 0.2 pixel scale
config.warpAndPsfMatch.psfMatch.kernel["AL"].alardSigGauss = [1.5, 3.0, 6.0]
config.warpAndPsfMatch.psfMatch.kernel["AL"].sizeCellX = 256
config.warpAndPsfMatch.psfMatch.kernel["AL"].sizeCellY = 256
