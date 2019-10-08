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

import lsst.afw.fits
from .lsstCamMapper import assemble_raw
from .assembly import readRawAmps


def readRawFile(fileName, detector, dataId=None):
    """Read a raw file from fileName, assembling it nicely.

    Parameters
    ----------
    filename : `str`
        The fully-qualified filename.
    detector : `lsst.afw.cameraGeom.Detector`
        Detector to associate with the returned Exposure.
    dataId : `lsst.daf.persistence.DataId` or `dict`
        DataId to use in log message output.

    Returns
    -------
    exposure : `lsst.afw.image.Exposure`
        The assembled exposure from the supplied filename.
    """
    if dataId is None:
        dataId = {}

    class Info():
        def __init__(self, obj):
            self.obj = obj

    amps = readRawAmps(fileName, detector=detector)

    component_info = {}
    component_info["raw_hdu"] = Info(lsst.afw.fits.readMetadata(fileName, hdu=0))
    component_info["raw_amp"] = Info(amps)

    exp = assemble_raw(dataId, component_info, None)

    return exp
