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
#

"""
Miscellaneous utilities related to lsst cameras
"""

__all__ = ("readRawFile",)

from .assembly import attachRawWcsFromBoresight, readRawAmps, fixAmpsAndAssemble
from ._fitsHeader import readRawFitsHeader


def readRawFile(fileName, detector, dataId=None):
    """Read a raw file from fileName, assembling it nicely.

    Parameters
    ----------
    filename : `str`
        The fully-qualified filename.
    detector : `lsst.afw.cameraGeom.Detector`
        Detector to associate with the returned Exposure.
    dataId : `lsst.daf.butler.DataCoordinate` or `dict`
        DataId to use in log message output.

    Returns
    -------
    exposure : `lsst.afw.image.Exposure`
        The assembled exposure from the supplied filename.
    """
    if dataId is None:
        dataId = {}

    amps = readRawAmps(fileName, detector=detector)
    exp = fixAmpsAndAssemble(amps, str(dataId))
    md = readRawFitsHeader(fileName)
    exp.setMetadata(md)
    attachRawWcsFromBoresight(exp, dataId)
    return exp
