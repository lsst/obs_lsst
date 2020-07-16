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
import traceback
from lsst.afw.cameraGeom import PIXELS, FIELD_ANGLE
from lsst.afw.geom.skyWcs import makeSkyWcs
from lsst.afw.image import RotType
import lsst.log
from lsst.obs.base.utils import InitialSkyWcsError
from . import LsstCamMapper, LsstCamMakeRawVisitInfo
from .ingest import LsstCamParseTask
from .translators import LatissTranslator
from .filters import LATISS_FILTER_DEFINITIONS
from ._instrument import Latiss

__all__ = ["LatissMapper", "LatissParseTask"]


class LatissMakeRawVisitInfo(LsstCamMakeRawVisitInfo):
    """Make a VisitInfo from the FITS header of a raw image."""
    metadataTranslator = LatissTranslator


class LatissMapper(LsstCamMapper):
    """The Mapper for the LATISS camera."""

    MakeRawVisitInfoClass = LatissMakeRawVisitInfo
    _gen3instrument = Latiss

    _cameraName = "latiss"
    yamlFileList = ["latiss/latissMapper.yaml"] + list(LsstCamMapper.yamlFileList)
    filterDefinitions = LATISS_FILTER_DEFINITIONS

    def _extractDetectorName(self, dataId):
        return f"{LatissTranslator.DETECTOR_GROUP_NAME}_{LatissTranslator.DETECTOR_NAME}"

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
            if "controller" in dataId:
                controller = dataId["controller"]
            else:
                lsst.log.Log.getLogger("LsstLatissMapper").warn("Controller unknown, using 'C'")
                controller = "C"
            visit = LatissTranslator.compute_exposure_id(dataId['dayObs'], dataId["seqNum"],
                                                         controller)

        if "detector" in dataId:
            detector = dataId["detector"]
            if detector != 0:
                lsst.log.Log.getLogger("LatissMapper").warn("Got detector %d for LATISS when it should"
                                                            " always be 0", detector)
        else:
            detector = 0

        return LatissTranslator.compute_detector_exposure_id(visit, detector)

    def _standardizeExposure(self, mapping, item, dataId, filter=True, trimmed=True, setVisitInfo=True):
        """Defer to the base class, except for the initial wcs creation."""
        exposure = super()._standardizeExposure(mapping, item, dataId, filter=filter,
                                                trimmed=trimmed, setVisitInfo=setVisitInfo)
        if mapping.level.lower() != "amp":
            self._createInitialSkyWcs(exposure)
        return exposure

    def _createInitialSkyWcs(self, exposure, extraRotationDegrees=None, translationXy=None):
        # LATISS has a coordinate system flipped in Y with respect to our
        # VisitInfo definition of the field angle orientation.
        # We have to override this method until RFC-605 is implemented, to pass
        # `flipX=True` to createInitialSkyWcs below and add the necessary 180
        # deg rotation on top to turn the flipX into a flipY

        if exposure.getInfo().getVisitInfo() is None:
            msg = "No VisitInfo; cannot access boresight information. Defaulting to metadata-based SkyWcs."
            self.log.warn(msg)
            return
        try:
            detector = exposure.getDetector()
            visitInfo = exposure.getInfo().getVisitInfo()
            rotAngle = visitInfo.getBoresightRotAngle()
            boresight = visitInfo.getBoresightRaDec()
            pixelsToFieldAngle = detector.getTransform(detector.makeCameraSys(PIXELS),
                                                       detector.makeCameraSys(FIELD_ANGLE))

            if visitInfo.getRotType() != RotType.SKY:
                msg = (f"Cannot create SkyWcs from camera geometry: rotator angle defined using "
                       f"RotType={visitInfo.getRotType()} instead of SKY.")
                raise InitialSkyWcsError(msg)

            flipX = True
            wcs = makeSkyWcs(pixelsToFieldAngle, rotAngle, flipX, boresight)

            exposure.setWcs(wcs)
            return
        except lsst.pex.exceptions.InvalidParameterError as e:
            raise InitialSkyWcsError("Cannot compute PIXELS to FIELD_ANGLE Transform.") from e
        except InitialSkyWcsError as e:
            msg = "Cannot create SkyWcs using VisitInfo and Detector, using metadata-based SkyWcs: %s"
            self.log.warn(msg, e)
            self.log.debug("Exception was: %s", traceback.TracebackException.from_exception(e))
            if e.__context__ is not None:
                self.log.debug("Root-cause Exception was: %s",
                               traceback.TracebackException.from_exception(e.__context__))


class LatissParseTask(LsstCamParseTask):
    """Parser suitable for LATISS raw data.
    """

    _mapperClass = LatissMapper
    _translatorClass = LatissTranslator

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
            logger = lsst.log.Log.getLogger('obs.lsst.LatissParseTask')
            logger.warn(
                'Could not determine sequence number. Assuming %d ', seqNum)

        return seqNum
