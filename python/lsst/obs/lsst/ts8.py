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
from .translators import LsstTS8Translator
from ._instrument import LsstTS8

__all__ = ["Ts8Mapper", "Ts8ParseTask"]


class Ts8MakeRawVisitInfo(LsstCamMakeRawVisitInfo):
    """Make a VisitInfo from the FITS header of a raw image."""
    metadataTranslator = LsstTS8Translator


class Ts8Mapper(LsstCamMapper):
    """The Mapper for the ts8 camera."""
    translatorClass = LsstTS8Translator
    MakeRawVisitInfoClass = Ts8MakeRawVisitInfo
    _gen3instrument = LsstTS8
    _cameraName = "ts8"
    yamlFileList = ["ts8/ts8Mapper.yaml"] + list(LsstCamMapper.yamlFileList)
    filterDefinitions = LsstTS8.filterDefinitions

    def _computeCcdExposureId(self, dataId):
        """Compute the 64-bit (long) identifier for a CCD exposure.

        Parameters
        ----------
        dataId : `dict`
            Data identifier including ``dayObs`` and ``seqNum``.
        """
        if len(dataId) == 0:
            return 0                    # give up.  Useful if reading files without a butler

        return super()._computeCcdExposureId(dataId)

    def bypass_ccdExposureId_bits(self, datasetType, pythonType, location, dataId):
        """How many bits are required for the maximum exposure ID"""
        return 58  # max detector_exposure_id ~ 203012122359599500


class Ts8ParseTask(LsstCamParseTask):
    """Parser suitable for ts8 data.
    """

    _mapperClass = Ts8Mapper
    _translatorClass = LsstTS8Translator

    def translate_testSeqNum(self, md):
        """Translate the sequence number.

        Sometimes this is present, sometimes it is not. When it is, return it
        as an int. When it's not, provide a default value of 0 as an int.
        This function exists because currently the Gen2 butler's default
        value providing pathway has trouble with types.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            Image metadata.

        Returns
        -------
        seqNum : `int`
            The seqNum, with a default value of ``0`` if required.
        """
        try:
            seqNum = md.getScalar("SEQNUM")
        except KeyError:
            seqNum = 0
        return seqNum
