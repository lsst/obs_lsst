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

from lsst.utils import getPackageDir
from lsst.meas.base import CircularApertureFluxAlgorithm

config.measurement.load(os.path.join(getPackageDir("obs_lsst"), "config", "apertures.py"))
config.measurement.load(os.path.join(getPackageDir("obs_lsst"), "config", "kron.py"))
config.measurement.load(os.path.join(getPackageDir("obs_lsst"), "config", "convolvedFluxes.py"))
config.load(os.path.join(getPackageDir("obs_lsst"), "config", "cmodel.py"))

config.measurement.slots.gaussianFlux = None

if 'BRIGHT_OBJECT' not in config.measurement.plugins['base_PixelFlags'].masksFpCenter:
    config.measurement.plugins['base_PixelFlags'].masksFpCenter.append('BRIGHT_OBJECT')
if 'BRIGHT_OBJECT' not in config.measurement.plugins['base_PixelFlags'].masksFpAnywhere:
    config.measurement.plugins['base_PixelFlags'].masksFpAnywhere.append('BRIGHT_OBJECT')

config.catalogCalculation.plugins.names = ["base_ClassificationExtendedness"]
config.measurement.slots.psfFlux = "base_PsfFlux"

def doUndeblended(config, algName, fluxList=None):
    """Activate undeblended measurements of algorithm
    Parameters
    ----------
    algName : `str`
        Algorithm name.
    fluxList : `list` of `str`, or `None`
        List of flux columns to register for aperture correction. If `None`,
        then this will be the `algName` appended with `_flux`.
    """
    if algName not in config.measurement.plugins:
        return
    if fluxList is None:
        fluxList = [algName + "_flux"]
    config.measurement.undeblended.names.add(algName)
    config.measurement.undeblended[algName] = config.measurement.plugins[algName]
    for flux in fluxList:
        config.applyApCorr.proxies["undeblended_" + flux] = flux


doUndeblended(config, "base_PsfFlux")
doUndeblended(config, "ext_photometryKron_KronFlux")
doUndeblended(config, "base_CircularApertureFlux", [])  # No aperture correction for circular apertures
doUndeblended(config, "ext_convolved_ConvolvedFlux",
              config.measurement.plugins["ext_convolved_ConvolvedFlux"].getAllResultNames())
# Disable registration for apCorr of undeblended convolved; apCorr will be done through the deblended proxy
config.measurement.undeblended["ext_convolved_ConvolvedFlux"].registerForApCorr = False
