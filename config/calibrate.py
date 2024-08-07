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

from lsst.meas.algorithms import ColorLimit

obsConfigDir = os.path.dirname(__file__)

config.photoCal.match.referenceSelection.magLimit.fluxField = "r_flux"
colors = config.photoCal.match.referenceSelection.colorLimits
colors["g-r"] = ColorLimit(primary="g_flux", secondary="r_flux", minimum=0.4, maximum=2.0)

# TODO: Turn color terms back on when they are available
config.photoCal.applyColorTerms = False
config.photoCal.photoCatName = "atlas_refcat2_20220201"

# Activate calibration of measurements: required for aperture corrections
config.measurement.load(os.path.join(obsConfigDir, "apertures.py"))
config.measurement.load(os.path.join(obsConfigDir, "kron.py"))
config.measurement.load(os.path.join(obsConfigDir, "hsm.py"))

config.measurement.plugins.names |= ["base_Jacobian", "base_FPPosition"]

config.measurement.plugins["base_Jacobian"].pixelScale = 0.2

config.connections.astromRefCat = "gaia_dr3_20230707"
config.connections.photoRefCat = "atlas_refcat2_20220201"
