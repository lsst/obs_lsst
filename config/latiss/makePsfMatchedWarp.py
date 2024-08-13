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

"""LATISS-specific overrides for MakePsfMatchedWarpTask"""

# PSF-matching configs are in units of pix and specific to skymap pixel scale

# Max PSF FWHM allowed into coadds BestSeeingSelectVisits.maxPsfFwhm = 1.9
# If skymap pixel scale is 0.1, that translates to Fwhm of 19.0
# TO DO: Change this to 9.5 if we go to 0.2 pixel scale.
config.modelPsf.defaultFwhm = 19.0

# These configs are for skymaps of pixel scale 0.1
# TO DO: Delete these 5 if we go a 0.2 pixel scale
config.psfMatch.kernel['AL'].kernelSize = 43
config.psfMatch.kernel['AL'].alardSigGauss = [1.5, 3.0, 6.0]
config.psfMatch.kernel['AL'].sizeCellX = 256
config.psfMatch.kernel['AL'].sizeCellY = 256
