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
import os.path

obsConfigDir = os.path.dirname(__file__)

config.isr.doCrosstalk=False

# Use Gaia-DR2 for astrometric calibration, and Panstarrs-1 DR1 for photometric
# calibration and for identifying stars for PSF measurements.
config.calibrate.astromRefObjLoader.ref_dataset_name = "gaia_dr2_20200414"
config.calibrate.astromRefObjLoader.load(os.path.join(obsConfigDir, "gaiaFilterMap.py"))

config.calibrate.photoRefObjLoader.ref_dataset_name = "ps1_pv3_3pi_20170110"
config.calibrate.photoRefObjLoader.load(os.path.join(obsConfigDir, "filterMap.py"))
config.calibrate.photoCal.match.referenceSelection.magLimit.fluxField = "i_flux"
config.charImage.refObjLoader.ref_dataset_name = config.calibrate.photoRefObjLoader.ref_dataset_name
config.charImage.refObjLoader.load(os.path.join(obsConfigDir, "filterMap.py"))

# gen3 consistency settings for the above
config.calibrate.connections.astromRefCat = config.calibrate.astromRefObjLoader.ref_dataset_name
config.calibrate.connections.photoRefCat = config.calibrate.photoRefObjLoader.ref_dataset_name

# Demand astrometry and photoCal succeed
config.calibrate.requireAstrometry = False
config.calibrate.requirePhotoCal = False

config.calibrate.photoCal.reserve.fraction = 0.0
config.charImage.measurePsf.reserve.fraction = 0.0
config.charImage.measurePsf.starSelector["objectSize"].doFluxLimit = True
config.charImage.measurePsf.starSelector["objectSize"].fluxMin = 4000
config.charImage.measurePsf.starSelector["objectSize"].doSignalToNoiseLimit = True

config.charImage.measurement.plugins["base_Jacobian"].pixelScale = 0.1  # arcsec/pix
config.calibrate.measurement.plugins["base_Jacobian"].pixelScale = 0.1  # arcsec/pix
