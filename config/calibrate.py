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
LSST Cam-specific overrides for CalibrateTask
"""
import os.path

obsConfigDir = os.path.join(os.path.dirname(__file__))

# Enable temporary local background subtraction
config.detection.doTempLocalBackground  = True

# Set to match defaults currenyly used in HSC production runs (e.g. S15B)
config.catalogCalculation.plugins['base_ClassificationExtendedness'].fluxRatio = 0.95

# Detection
config.detection.isotropicGrow = True

# Activate calibration of measurements: required for aperture corrections
config.measurement.load(os.path.join(obsConfigDir, "apertures.py"))
config.measurement.load(os.path.join(obsConfigDir, "kron.py"))
config.measurement.load(os.path.join(obsConfigDir, "hsm.py"))

# Deblender
config.deblend.maxFootprintSize = 0
config.deblend.maskLimits["NO_DATA"] = 0.25 # Ignore sources that are in the vignetted region
config.deblend.maxFootprintArea = 10000

config.measurement.plugins.names |= ["base_Jacobian", "base_FPPosition"]

config.measurement.plugins["base_Jacobian"].pixelScale = 0.2

# Prevent spurious detections in vignetting areas
config.detection.thresholdType = 'pixel_stdev'
