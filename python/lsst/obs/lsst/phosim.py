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
from .translators import PhosimTranslator

__all__ = ["PhosimMapper", "PhosimParseTask", "PhosimEimgParseTask"]


class PhosimRawVisitInfo(LsstCamMakeRawVisitInfo):
    """Make a VisitInfo from the FITS header of a raw image."""
    metadataTranslator = PhosimTranslator


class PhosimMapper(LsstCamMapper):
    """The Mapper for the phosim simulations of the LsstCam."""
    translatorClass = PhosimTranslator
    MakeRawVisitInfoClass = PhosimRawVisitInfo

    _cameraName = "phosim"

    def bypass_ccdExposureId_bits(self, datasetType, pythonType, location, dataId):
        """How many bits are required for the maximum exposure ID"""
        return 38  # max detector_exposure_id ~ 60000000205


class PhosimParseTask(LsstCamParseTask):
    """Parser suitable for phosim data.
    """

    _mapperClass = PhosimMapper
    _translatorClass = PhosimTranslator

    def translate_controller(self, md):
        """Always return Simulation as controller for imsim data."""
        return "S"


class PhosimEimgParseTask(PhosimParseTask):
    """Parser suitable for phosim eimage data.
    """

    def getDestination(self, butler, info, filename):
        """Get destination for the file.

        Parameters
        ----------
        butler : `lsst.daf.persistence.Butler`
            Data butler
        info : data ID
            File properties, used as dataId for the butler.
        filename : `str`
            Input filename.

        Returns
        -------
        `str`
            Destination filename.
        """

        eimage = butler.get("eimage_filename", info)[0]
        # Ensure filename is devoid of cfitsio directions about HDUs
        c = eimage.find("[")
        if c > 0:
            eimage = eimage[:c]
        return eimage
