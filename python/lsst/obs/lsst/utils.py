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

import lsst.afw.image as afwImage
from lsst.obs.lsst.lsstCamMapper import assemble_raw
try:
    from lsst.obs.lsst.lsstCamMapper import _camera
except ImportError:
    from lsst.obs.lsst.auxTel import AuxTelMapper
    mapper = AuxTelMapper()    # Sets the sleazy _camera global

    from lsst.obs.lsst.lsstCamMapper import _camera


def readRawFile(fileName, dataId={}):
    """Read a raw file from fileName, assembling it nicely.

    Parameters
    ----------
    filename : `str`
        The fully-qualified filename.
    dataId : `lsst.daf.persistence.DataId`
        If provided, used to look up e.g. the filter.

    Returns
    -------
    exposure : `lsst.afw.image.Exposure`
        The assembled exposure from the supplied filename.
    """

    class Info():
        def __init__(self, obj):
            self.obj = obj

    amps = []
    for hdu in range(1, 16+1):
        exp = afwImage.makeExposure(afwImage.makeMaskedImage(afwImage.ImageF(fileName, hdu=hdu)))
        exp.setDetector(_camera[0])
        amps.append(exp)

    component_info = {}
    component_info["raw_hdu"] = Info(afwImage.readMetadata(fileName, hdu=0))
    component_info["raw_amp"] = Info(amps)

    exp = assemble_raw(dataId, component_info, None)

    return exp
