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
from . import LsstCamMapper, LsstCamMakeRawVisitInfo
from .ingest import LsstCamParseTask
from .translators import ImsimTranslator

__all__ = ["ImsimMapper", "ImsimParseTask"]


class ImsimMakeRawVisitInfo(LsstCamMakeRawVisitInfo):
    """Make a VisitInfo from the FITS header of a raw image."""
    metadataTranslator = ImsimTranslator


class ImsimMapper(LsstCamMapper):
    """The Mapper for the imsim simulations of the LsstCam."""
    translatorClass = ImsimTranslator
    MakeRawVisitInfoClass = ImsimMakeRawVisitInfo

    _cameraName = "imsim"


class ImsimParseTask(LsstCamParseTask):
    """Parser suitable for phosim data.
    """

    _mapperClass = ImsimMapper
