# Set up aperture photometry

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

# 'config' should be a SourceMeasurementConfig

config.plugins.names |= ["base_CircularApertureFlux"]
# TODO: these numbers assume an HSC plate scale!
# Roughly (1.0, 1.4, 2.0, 2.8, 4.0, 5.7, 8.0, 11.3, 16.0, 22.6 arcsec) in diameter: 2**(0.5*i)
# (assuming plate scale of 0.168 arcsec pixels)
config.plugins["base_CircularApertureFlux"].radii = [3.0, 4.5, 6.0, 9.0, 12.0, 17.0, 25.0, 35.0, 50.0, 70.0]

# Use a large aperture to be independent of seeing in calibration
config.plugins["base_CircularApertureFlux"].maxSincRadius = 12.0
