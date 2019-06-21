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
import os.path
import re
import lsst.log
from . import LsstCamMapper, LsstCamMakeRawVisitInfo
from .ingest import LsstCamParseTask
from .translators import LsstAuxTelTranslator

__all__ = ["AuxTelMapper", "AuxTelParseTask"]


class AuxTelMakeRawVisitInfo(LsstCamMakeRawVisitInfo):
    """Make a VisitInfo from the FITS header of a raw image."""
    metadataTranslator = LsstAuxTelTranslator


class AuxTelMapper(LsstCamMapper):
    """The Mapper for the auxTel camera."""

    MakeRawVisitInfoClass = AuxTelMakeRawVisitInfo

    _cameraName = "auxTel"
    yamlFileList = ["auxTel/auxTelMapper.yaml"] + list(LsstCamMapper.yamlFileList)

    def _extractDetectorName(self, dataId):
        return f"{LsstAuxTelTranslator.DETECTOR_GROUP_NAME}_{LsstAuxTelTranslator.DETECTOR_NAME}"

    def _computeCcdExposureId(self, dataId):
        """Compute the 64-bit (long) identifier for a CCD exposure.

        Parameters
        ----------
        dataId : `dict`
            Data identifier including dayObs and seqNum.

        Returns
        -------
        id : `int`
            Integer identifier for a CCD exposure.
        """
        if len(dataId) == 0:
            return 0                    # give up.  Useful if reading files without a butler

        if 'visit' in dataId:
            visit = dataId['visit']
        else:
            visit = LsstAuxTelTranslator.compute_exposure_id(dataId['dayObs'], dataId["seqNum"])

        if "detector" in dataId:
            detector = dataId["detector"]
            if detector != 0:
                lsst.log.Log.getLogger("AuxTelMapper").warn("Got detector %d for AuxTel when it should"
                                                            " always be 0", detector)
        else:
            detector = 0

        return LsstAuxTelTranslator.compute_detector_exposure_id(visit, detector)


class AuxTelParseTask(LsstCamParseTask):
    """Parser suitable for auxTel data.
    """

    _mapperClass = AuxTelMapper
    _translatorClass = LsstAuxTelTranslator

    def translate_seqNum(self, md):
        """Return the sequence number.

        Parameters
        ----------
        md : `~lsst.daf.base.PropertyList` or `~lsst.daf.base.PropertySet`
            Image metadata.

        Returns
        -------
        seqnum : `int`
            The sequence number identifier valid within a day.
        """

        if "SEQNUM" in md:
            return md.getScalar("SEQNUM")
        #
        # Oh dear.  Extract it from the filename
        #
        seqNum = 0
        for k in ("IMGNAME", "FILENAME"):
            if k not in md:
                continue
            name = md.getScalar(k)           # e.g. AT-O-20180816-00008
            # Trim trailing extensions
            name = os.path.splitext(name)[0]

            # Want final digits
            mat = re.search(r"(\d+)$", name)
            if mat:
                seqNum = int(mat.group(1))    # 00008
                break

        if seqNum == 0:
            logger = lsst.log.Log.getLogger('obs.lsst.AuxTelParseTask')
            logger.warn(
                'Could not determine sequence number. Assuming %d ', seqNum)

        return seqNum
