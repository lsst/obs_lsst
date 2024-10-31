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

"""LSSTComCam-specific overrides for MakeWarpTask"""

# These thresholds are being set quite loosely for early LSSTComCam
# commissioning to make sure we get most of the processed visits
# included in the coadds.  These have been chosen based on the data
# in the LSSTComCam/nightlyValidation collection in the embargo_new
# repo on Oct 30, 2024.
config.select.maxEllipResidual = 0.19
config.select.maxScaledSizeScatter = 0.07
config.select.maxPsfTraceRadiusDelta = 1.2
config.select.maxPsfApFluxDelta = 0.19
config.select.maxPsfApCorrSigmaScaledDelta = 0.15

# PSF-matching configs are in units of pix and specific to skymap pixel scale.

# Currently allowing BestSeeingSelectVisits.maxPsfFwhm = 2.7 into coadds, so
# increase the default PSF fwhm (pixels) size.
# TODO DM-47171: optimize this config setting for artifact rejection.
config.modelPsf.defaultFwhm = 11.0
